import os
import sys
import logging
import argparse
import shutil
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dataclasses import dataclass
from typing import Optional, List, Dict
from dotenv import load_dotenv
import pickle

import google_auth_oauthlib.flow
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Auto-create .env from env.example if it doesn't exist
def ensure_env_file():
    """Create .env from env.example if it doesn't exist"""
    env_file = '.env'
    env_example = 'env.example'
    
    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            shutil.copy(env_example, env_file)
            logger.info(f"Created {env_file} from {env_example}")
            logger.info(f"Please edit {env_file} with your configuration before running again")
            sys.exit(0)
        else:
            logger.error(f"Neither {env_file} nor {env_example} found")
            sys.exit(1)

ensure_env_file()

# Load environment variables
load_dotenv()


@dataclass
class ServiceConfig:
    """Configuration for a service stream"""
    service_id: str  # A, B, C, etc.
    name: str
    day_of_week: int  # 0=Monday, 5=Saturday, 6=Sunday
    time_hour: int
    time_minute: int
    description: str = ""


class YouTubeStreamScheduler:
    """YouTube Live Stream Scheduler"""
    
    # Day name to weekday number mapping
    DAY_MAPPING = {
        'MONDAY': 0, 'TUESDAY': 1, 'WEDNESDAY': 2, 'THURSDAY': 3,
        'FRIDAY': 4, 'SATURDAY': 5, 'SUNDAY': 6
    }
    
    def __init__(self, weeks: Optional[int] = None):
        """Initialize the scheduler with configuration from environment"""
        self.oauth2_credentials_file = os.getenv('OAUTH2_CREDENTIALS_FILE')
        self.channel_id = os.getenv('CHANNEL_ID')
        self.playlist_id = os.getenv('PLAYLIST_ID')
        self.campus_name = os.getenv('CAMPUS_NAME', 'Fishers')
        self.timezone = ZoneInfo(os.getenv('TIMEZONE', 'America/Indianapolis'))
        self.privacy_status = os.getenv('PRIVACY_STATUS', 'unlisted')
        self.made_for_kids = os.getenv('MADE_FOR_KIDS', 'false').lower() == 'true'
        self.dry_run = os.getenv('DRY_RUN', 'false').lower() == 'true'
        
        # Parse enabled services
        enabled_services_str = os.getenv('ENABLED_SERVICES', '')
        self.enabled_service_names = [s.strip().upper() for s in enabled_services_str.split(',') if s.strip()]
        
        # Load service configurations from environment
        self.services = self._load_service_configs()
        
        # Handle weeks parameter
        if weeks is not None and weeks > 0:
            # Calculate date range from weeks argument
            now = datetime.now(self.timezone)
            self.start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = self.start_date + timedelta(weeks=weeks)
            logger.info(f"Scheduling {weeks} week(s) of services")
        else:
            # No weeks specified, schedule next occurrence only
            self.start_date = None
            self.end_date = None
        
        self.youtube = None
        self.existing_streams = []
        self.stream_mapping = {}  # Will map service letter to stream object
    
    def _load_service_configs(self) -> Dict[str, ServiceConfig]:
        """Load service configurations from environment variables"""
        services = {}
        
        for service_id in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            name = os.getenv(f'SERVICE_{service_id}_NAME')
            day_str = os.getenv(f'SERVICE_{service_id}_DAY', '').strip().upper()
            time_str = os.getenv(f'SERVICE_{service_id}_TIME', '').strip()
            description = os.getenv(f'SERVICE_{service_id}_DESCRIPTION', '').strip()
            
            # Skip if essential config is missing
            if not name:
                continue
            
            # Parse day of week
            day_of_week = None
            if day_str and day_str in self.DAY_MAPPING:
                day_of_week = self.DAY_MAPPING[day_str]
            
            # Parse time
            time_hour = None
            time_minute = None
            if time_str and ':' in time_str:
                try:
                    time_parts = time_str.split(':')
                    time_hour = int(time_parts[0])
                    time_minute = int(time_parts[1])
                except (ValueError, IndexError):
                    logger.warning(f"Invalid time format for SERVICE_{service_id}_TIME: {time_str}")
            
            # Create service config
            services[service_id] = ServiceConfig(
                service_id=service_id,
                name=name,
                day_of_week=day_of_week,
                time_hour=time_hour,
                time_minute=time_minute,
                description=description
            )
        
        return services
    
    def validate_config(self) -> bool:
        """Validate required configuration"""
        errors = []
        
        if not self.oauth2_credentials_file:
            errors.append("OAUTH2_CREDENTIALS_FILE is required")
        elif not os.path.exists(self.oauth2_credentials_file):
            errors.append(f"OAuth2 credentials file not found: {self.oauth2_credentials_file}")
            
        if not self.channel_id:
            errors.append("CHANNEL_ID is required")
            
        if not self.playlist_id:
            errors.append("PLAYLIST_ID is required")
            
        if not self.enabled_service_names:
            errors.append("ENABLED_SERVICES is required")
            
        # Validate service configurations exist for enabled services
        for service_id in self.enabled_service_names:
            if service_id not in self.services:
                errors.append(f"Service {service_id} is not configured. Need SERVICE_{service_id}_NAME")
            else:
                service = self.services[service_id]
                # All services must have a schedule configured
                if service.day_of_week is None or service.time_hour is None:
                    errors.append(f"Service {service_id} ({service.name}) has no schedule configured. Set SERVICE_{service_id}_DAY and SERVICE_{service_id}_TIME")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
            
        return True
    
    def authenticate(self):
        """Authenticate with YouTube API using persistent token"""
        try:
            scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
            token_file = "token.pickle"
            credentials = None
            
            # Load saved credentials if they exist
            if os.path.exists(token_file):
                logger.info("Loading saved credentials...")
                with open(token_file, 'rb') as token:
                    credentials = pickle.load(token)
            
            # If credentials don't exist or are invalid, get new ones
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    logger.info("Refreshing expired credentials...")
                    try:
                        credentials.refresh(Request())
                        logger.info("Credentials refreshed successfully")
                    except Exception as e:
                        logger.warning(f"Failed to refresh credentials: {e}")
                        credentials = None
                
                if not credentials:
                    logger.info("Authenticating with YouTube API (browser will open)...")
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        self.oauth2_credentials_file, scopes
                    )
                    credentials = flow.run_local_server(port=0)
                    logger.info("Authentication successful")
                
                # Save credentials for future use
                with open(token_file, 'wb') as token:
                    pickle.dump(credentials, token)
                    logger.info("Credentials saved for future use")
            else:
                logger.info("Using saved credentials")
            
            self.youtube = googleapiclient.discovery.build(
                "youtube", "v3", credentials=credentials
            )
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def fetch_existing_streams(self):
        """Fetch existing live streams from YouTube and auto-map them"""
        try:
            logger.info("Fetching existing live streams...")
            response = self.youtube.liveStreams().list(
                part="id,snippet",
                maxResults=50,
                mine=True
    ).execute()

            self.existing_streams = response.get("items", [])
            logger.info(f"Found {len(self.existing_streams)} existing streams")
            
            # Auto-detect and map streams based on naming pattern: "{CAMPUS_NAME} Stream {Letter}"
            self.stream_mapping = {}
            expected_pattern = f"{self.campus_name} Stream "
            
            for stream in self.existing_streams:
                title = stream.get('snippet', {}).get('title', '')
                if title.startswith(expected_pattern):
                    # Extract the letter (A, B, C, etc.)
                    letter = title[len(expected_pattern):].strip()
                    if len(letter) == 1 and letter.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
                        self.stream_mapping[letter.upper()] = stream
                        logger.info(f"Auto-mapped service {letter.upper()} to stream: {title}")
            
            if not self.stream_mapping:
                logger.warning(f"No streams found matching pattern '{expected_pattern}[A-H]'")
            
            return self.existing_streams
            
        except googleapiclient.errors.HttpError as e:
            logger.error(f"Failed to fetch existing streams: {e}")
            raise
    
    def get_stream_by_service_id(self, service_id: str) -> Optional[Dict]:
        """Get stream for a service by its ID (A-H)"""
        if service_id in self.stream_mapping:
            stream = self.stream_mapping[service_id]
            logger.info(f"Selected stream for service {service_id}: {stream.get('snippet', {}).get('title', 'Unknown')}")
            return stream
        logger.error(f"No stream found for service {service_id}. Expected stream name: '{self.campus_name} Stream {service_id}'")
        return None
    
    def calculate_next_occurrence(self, day_of_week: int, hour: int, minute: int) -> datetime:
        """Calculate the next occurrence of a specific day/time"""
        now = datetime.now(self.timezone)
        
        # Calculate days until target day
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        next_date = now + timedelta(days=days_ahead)
        next_datetime = next_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # If the calculated time is in the past (shouldn't happen with days_ahead logic, but just in case)
        if next_datetime <= now:
            next_datetime += timedelta(days=7)
        
        return next_datetime
    
    def get_service_dates(self, service_id: str) -> List[datetime]:
        """Get list of dates for a service based on weeks parameter"""
        if service_id not in self.services:
            logger.warning(f"Service {service_id} is not configured")
            return []
        
        service = self.services[service_id]
        dates = []
        
        if self.start_date and self.end_date:
            # Week range mode: find all occurrences within range
            current = self.start_date
            while current <= self.end_date:
                if current.weekday() == service.day_of_week:
                    service_time = current.replace(
                        hour=service.time_hour,
                        minute=service.time_minute,
                        second=0,
                        microsecond=0
                    )
                    if self.start_date <= service_time <= self.end_date:
                        dates.append(service_time)
                current += timedelta(days=1)
        else:
            # Default mode: next occurrence only
            next_date = self.calculate_next_occurrence(
                service.day_of_week,
                service.time_hour,
                service.time_minute
            )
            dates.append(next_date)
        
        return dates
    
    def format_stream_title(self, service_datetime: datetime) -> str:
        """Format stream title with campus name and date/time"""
        formatted = service_datetime.strftime('%m-%d-%Y // %I:%M %p')
        return f"{self.campus_name} // {formatted}"
    
    def create_broadcast(self, service: ServiceConfig, scheduled_time: datetime) -> Optional[str]:
        """Create a YouTube live broadcast"""
        try:
            stream = self.get_stream_by_service_id(service.service_id)
            if not stream:
                logger.error(f"Stream not found for service {service.service_id} ({service.name})")
                return None
            
            stream_title = self.format_stream_title(scheduled_time)
            scheduled_time_iso = scheduled_time.isoformat()
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create broadcast:")
                logger.info(f"  Service: {service.service_id} - {service.name}")
                logger.info(f"  Title: {stream_title}")
                logger.info(f"  Time: {scheduled_time_iso}")
                logger.info(f"  Stream: {stream.get('snippet', {}).get('title', 'Unknown')}")
                logger.info(f"  Description: {service.description or 'No description'}")
                return None
            
            # Create live broadcast
            live_broadcast = self.youtube.liveBroadcasts().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": stream_title,
                        "description": service.description,
                        "scheduledStartTime": scheduled_time_iso,
                        "channelId": self.channel_id,
                    },
                    "status": {
                        "privacyStatus": self.privacy_status,
                        "selfDeclaredMadeForKids": self.made_for_kids,
                    }
                }
            ).execute()

            broadcast_id = live_broadcast["id"]
            logger.info(f"Created broadcast {broadcast_id}: {stream_title}")
            
            # Bind the broadcast to the stream
            self.youtube.liveBroadcasts().bind(
        part="id,contentDetails",
                id=broadcast_id,
                streamId=stream["id"],
    ).execute()

            logger.info(f"Bound broadcast to stream: {stream.get('snippet', {}).get('title', 'Unknown')}")
            
            # Add to playlist
            self.youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                        "playlistId": self.playlist_id,
                "position": 0,
                "resourceId": {
                    "kind": "youtube#video",
                            "videoId": broadcast_id,
                },
            },
        },
    ).execute()

            logger.info(f"Added broadcast to playlist")
            
            return broadcast_id
            
        except googleapiclient.errors.HttpError as e:
            logger.error(f"Failed to create broadcast for service {service.service_id} ({service.name}): {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating broadcast for service {service.service_id} ({service.name}): {e}")
            return None
    
    def remove_all_scheduled_broadcasts(self):
        """Remove all scheduled/upcoming broadcasts"""
        try:
            logger.info("Fetching all scheduled broadcasts...")
            
            # Fetch all upcoming broadcasts
            response = self.youtube.liveBroadcasts().list(
                part="id,snippet,status",
                broadcastStatus="upcoming",
                maxResults=50
            ).execute()
            
            broadcasts = response.get("items", [])
            
            if not broadcasts:
                logger.info("No scheduled broadcasts found to remove.")
                return 0
            
            logger.info(f"Found {len(broadcasts)} scheduled broadcast(s)")
            
            if self.dry_run:
                logger.info("[DRY RUN] Would delete the following broadcasts:")
                for broadcast in broadcasts:
                    title = broadcast.get('snippet', {}).get('title', 'Unknown')
                    scheduled_time = broadcast.get('snippet', {}).get('scheduledStartTime', 'Unknown')
                    broadcast_id = broadcast.get('id', 'Unknown')
                    logger.info(f"  - {title} @ {scheduled_time} (ID: {broadcast_id})")
                return len(broadcasts)
            
            # Delete each broadcast
            deleted_count = 0
            for broadcast in broadcasts:
                broadcast_id = broadcast.get('id')
                title = broadcast.get('snippet', {}).get('title', 'Unknown')
                
                try:
                    self.youtube.liveBroadcasts().delete(id=broadcast_id).execute()
                    logger.info(f"Deleted: {title} (ID: {broadcast_id})")
                    deleted_count += 1
                except googleapiclient.errors.HttpError as e:
                    logger.error(f"Failed to delete broadcast {broadcast_id}: {e}")
            
            logger.info(f"Successfully deleted {deleted_count} broadcast(s)")
            return deleted_count
            
        except googleapiclient.errors.HttpError as e:
            logger.error(f"Failed to fetch broadcasts: {e}")
            raise
    
    def run(self):
        """Main execution flow"""
        logger.info("YouTube Stream Scheduler Starting...")
        
        if self.dry_run:
            logger.info("Running in DRY RUN mode - no broadcasts will be created")
        
        # Validate configuration
        if not self.validate_config():
            logger.error("Configuration validation failed. Please check your .env file")
            sys.exit(1)
        
        # Authenticate
        self.authenticate()
        
        # Fetch existing streams
        self.fetch_existing_streams()
        
        if not self.existing_streams:
            logger.error("No existing stream keys found. Please set up stream keys in YouTube first.")
            sys.exit(1)
        
        # Determine mode
        if self.start_date and self.end_date:
            logger.info(f"Scheduling services from {self.start_date.date()} to {self.end_date.date()}")
        else:
            logger.info("Scheduling next occurrence of each service")
        
        # Process each enabled service
        total_created = 0
        for service_id in self.enabled_service_names:
            logger.info(f"\n--- Processing Service {service_id} ---")
            
            if service_id not in self.services:
                logger.warning(f"Service {service_id} is not configured, skipping")
                continue
            
            service = self.services[service_id]
            logger.info(f"Service Name: {service.name}")
            
            dates = self.get_service_dates(service_id)
            
            if not dates:
                logger.warning(f"No dates found for service {service_id}")
                continue
            
            logger.info(f"Found {len(dates)} date(s) for service {service_id}")
            
            for date in dates:
                logger.info(f"Scheduling for {date}")
                broadcast_id = self.create_broadcast(service, date)
                if broadcast_id:
                    total_created += 1
        
        logger.info(f"\n{'[DRY RUN] ' if self.dry_run else ''}Completed! {total_created} broadcast(s) {'would be ' if self.dry_run else ''}created.")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(
        description='YouTube Stream Scheduler - Automate scheduling of YouTube live broadcasts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                    # Schedule next occurrence of each service
  %(prog)s -w 4               # Schedule 4 weeks of services
  %(prog)s --weeks 52         # Schedule a full year (52 weeks)
  %(prog)s -w 1 --dry-run     # Preview 1 week without creating broadcasts
  %(prog)s --remove           # Remove all scheduled broadcasts
  %(prog)s --remove --dry-run # Preview what would be removed
        '''
    )
    
    parser.add_argument(
        '-w', '--weeks',
        type=int,
        metavar='N',
        help='Number of weeks to schedule'
    )
    
    parser.add_argument(
        '--remove', '-rm',
        action='store_true',
        help='Remove all scheduled/upcoming broadcasts'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview what would be created/removed without making actual changes'
    )
    
    args = parser.parse_args()
    
    # Override dry-run setting if specified on command line
    if args.dry_run:
        os.environ['DRY_RUN'] = 'true'
    
    scheduler = YouTubeStreamScheduler(weeks=args.weeks)
    
    # Handle remove mode
    if args.remove:
        # Authenticate (still needed for removal)
        scheduler.authenticate()
        scheduler.remove_all_scheduled_broadcasts()
    else:
        # Normal scheduling mode
        scheduler.run()


if __name__ == "__main__":
    main()
