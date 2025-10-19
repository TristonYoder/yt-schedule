# YouTube Stream Scheduler

Automated tool to schedule YouTube live broadcasts for recurring services and special events.

## Features

- Environment-based configuration through `.env` file
- Support for multiple services (A-H) with configurable stream keys
- Automatic scheduling calculations for recurring services
- Date range mode for scheduling multiple services across custom periods
- Dry run mode for preview without creating broadcasts
- Detailed logging and error handling

## Prerequisites

- Python 3.9 or higher
- Google Cloud Platform account
- YouTube channel with live streaming enabled
- Access to YouTube Data API v3

## Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd yt-schedule
```

2. **Install dependencies**

```bash
pip3 install -r requirements.txt
```

3. **Install the command-line tool**

```bash
pip3 install -e .
```

Verify installation:

```bash
yt-schedule --help
```

**Note**: If you skip this step, you can still use the tool by running `python3 main.py` from the project directory instead of `yt-schedule`.

## Configuration

### 1. Set Up Google Cloud Credentials

1. Navigate to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing project
3. Enable the YouTube Data API v3
4. Create OAuth 2.0 credentials (Desktop app type)
5. Download the credentials JSON file

### 2. Configure OAuth Credentials

Copy the example file and add your credentials:

```bash
cp OAuth2.json.example OAuth2.json
```

Edit `OAuth2.json` with your actual OAuth 2.0 credentials from Google Cloud Console.

**Security Note**: `OAuth2.json` and `token.pickle` are included in `.gitignore` and must never be committed to version control.

### 3. Configure Environment Variables

The `.env` file will be automatically created from `env.example` on first run. Alternatively, you can create it manually:

```bash
cp env.example .env
```

Edit `.env` with the following required settings:

**Required Settings**

- `CHANNEL_ID`: Your YouTube channel ID
- `PLAYLIST_ID`: Playlist ID where broadcasts will be added
- `CAMPUS_NAME`: Campus identifier for stream titles (e.g., "Fishers")
- `ENABLED_SERVICES`: Comma-separated list of services to schedule (e.g., "A,B,C,D,E,F")

**Service Configuration**

Configure each service (A-H) with the following variables:

- `SERVICE_X_NAME`: Display name (e.g., "Saturday 4:00pm Service")
- `SERVICE_X_DAY`: Day of week (Monday-Sunday)
- `SERVICE_X_TIME`: Time in 24-hour format (e.g., "16:00")
- `SERVICE_X_DESCRIPTION`: Optional broadcast description

**Optional Settings**

- `TIMEZONE`: Timezone for service times (default: `America/Indianapolis`)
- `PRIVACY_STATUS`: Broadcast privacy: `unlisted`, `private`, or `public` (default: `unlisted`)
- `AUTO_START`: Automatically start broadcast at scheduled time: `true` or `false` (default: `true`)
- `AUTO_STOP`: Automatically stop broadcast when stream ends: `true` or `false` (default: `true`)
- `ENABLE_DVR`: Enable DVR functionality for viewers: `true` or `false` (default: `true`)
- `ENABLE_360`: Enable 360° video mode: `true` or `false` (default: `false`)
- `DRY_RUN`: Enable preview mode: `true` or `false` (default: `false`)

### 4. Configure YouTube Stream Keys

The tool automatically detects stream keys based on the naming pattern:

```
{CAMPUS_NAME} Stream {Letter}
```

Example for `CAMPUS_NAME=Fishers`:
- `Fishers Stream A` → Service A
- `Fishers Stream B` → Service B

Configure your stream keys in YouTube Studio to match this naming pattern.

## Authentication

On first run, the tool will open a browser window for OAuth authentication:

1. Log in with your Google account
2. Grant the requested permissions
3. The tool will save credentials to `token.pickle`

Subsequent runs will use the saved credentials automatically. Credentials refresh automatically when they expire.

## Deployment

### Basic Usage
Schedule the next occurrence of each enabled service:

```bash
yt-schedule
```

This creates broadcasts for the next Saturday, Sunday, or Wednesday (depending on service configuration) and adds them to the specified playlist.

### Week Range Deployment

Schedule multiple weeks of services using the `-w` or `--weeks` flag:

```bash
yt-schedule -w 4
```

This schedules all enabled services for the next 4 weeks from today.

Examples:
- `yt-schedule -w 1` - Schedule 1 week
- `yt-schedule -w 12` - Schedule 3 months (12 weeks)
- `yt-schedule -w 52` - Schedule a full year

### Preview Mode (Dry Run)

Preview scheduled broadcasts without creating them:

```bash
yt-schedule --dry-run
```

Or configure in `.env`:

```env
DRY_RUN=true
```

### Remove Scheduled Broadcasts

Remove all upcoming/scheduled broadcasts:

```bash
yt-schedule --remove
```

Or use the shorthand:

```bash
yt-schedule -rm
```

Preview what would be removed without deleting:

```bash
yt-schedule --remove --dry-run
```

This is useful for:
- Clearing out old scheduled broadcasts before rescheduling
- Removing broadcasts that need to be rescheduled
- Cleaning up test broadcasts

## Usage Examples

### Schedule Weekend Services Only

Configure `.env`:

```env
ENABLED_SERVICES=A,B,C,D,E
```

Run the scheduler:

```bash
yt-schedule
```

### Schedule Multiple Weeks

Configure `.env`:

```env
ENABLED_SERVICES=A,B,C,D,E,F
```

Schedule 4 weeks of services:

```bash
yt-schedule -w 4
```

### Test Configuration

Preview the next week of services:

```bash
yt-schedule -w 1 --dry-run
```

## Service Defaults

Default service configurations (all times and names are customizable):

- **Service A**: Saturday 4:00pm Service
- **Service B**: Saturday 5:30pm Service
- **Service C**: Sunday 8:00am Service
- **Service D**: Sunday 9:30am Service
- **Service E**: Sunday 11:15am Service
- **Service F**: Wednesday 7:00pm Service
- **Service G**: Available for additional services (requires schedule configuration)
- **Service H**: Available for additional services (requires schedule configuration)

**Note**: All services must have a schedule configured (DAY and TIME). To use a service, set the appropriate environment variables in `.env`.

## Troubleshooting

### Authentication Errors

- Verify `OAuth2.json` exists and contains valid credentials
- Delete `token.pickle` and re-authenticate if credentials are corrupted
- Ensure the YouTube Data API v3 is enabled in Google Cloud Console

### No Streams Found

- Verify stream keys are configured in YouTube Studio
- Check stream key naming matches the pattern: `{CAMPUS_NAME} Stream {Letter}`
- Ensure `CAMPUS_NAME` in `.env` matches your stream key naming

### Incorrect Times

- Verify `TIMEZONE` setting matches your location
- Check service time configuration in `.env` uses 24-hour format
- Confirm `SERVICE_X_TIME` values are in `HH:MM` format

### Configuration Errors

- Verify all required environment variables are set in `.env`
- Check `ENABLED_SERVICES` only includes services that are fully configured
- Ensure date format is `YYYY-MM-DD` for `START_DATE` and `END_DATE`

## License

This tool is for internal use managing church service streams.
