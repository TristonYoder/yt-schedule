# YouTube Stream Scheduler

Automated tool to schedule YouTube live broadcasts for recurring services and special events.

## Features

- **Environment-based Configuration**: All settings managed through `.env` file
- **Multiple Services**: Support for services A-H with configurable stream keys
- **Auto Scheduling**: Automatically calculates next occurrence of each service
- **Date Range Mode**: Schedule multiple services across a custom date range
- **Dry Run Mode**: Preview what would be created without making changes
- **Proper Logging**: Detailed logging of all operations
- **Error Handling**: Graceful handling of API errors and configuration issues

## Services

Services A-H can be configured with custom names, schedules, and stream keys. By default:

- **A**: Saturday 4:00pm Service
- **B**: Saturday 5:30pm Service
- **C**: Sunday 8:00am Service
- **D**: Sunday 9:30am Service
- **E**: Sunday 11:15am Service
- **F**: Wednesday 7:00pm Service
- **G**: Special events (configure schedule as needed)
- **H**: Misc events (configure schedule as needed)

All service times and names are configurable via the `.env` file.

## Setup

1. **Install Dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure Environment**

Copy `env.example` to `.env` and update with your settings:

```bash
cp env.example .env
```

Edit `.env` with your:
- YouTube API credentials
- Channel ID and Playlist ID
- Enabled services
- Stream key mappings

3. **Set up YouTube API Credentials**

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a project and enable YouTube Data API v3
- Create OAuth 2.0 credentials (Desktop app type)
- Download the credentials JSON file
- Copy `OAuth2.json.example` to `OAuth2.json`
- Replace the placeholder values with your actual credentials

**Note on Authentication**: The first time you run the script, it will open a browser for authentication. After successful authentication, credentials are saved to `token.pickle` and subsequent runs will use the saved credentials without opening a browser. The credentials will be automatically refreshed when they expire.

**Security**: `OAuth2.json` and `token.pickle` are in `.gitignore` and should never be committed to version control.

## Usage

### Auto Mode (Next Occurrence)

Schedule the next occurrence of each enabled service:

```bash
python main.py
```

This will:
- Calculate the next Saturday/Sunday/Wednesday for each service
- Create broadcasts at the configured times
- Add them to your playlist

### Date Range Mode

Schedule services across a specific date range:

1. Edit `.env` and set:
```
START_DATE=2025-01-01
END_DATE=2025-01-31
```

2. Run the scheduler:
```bash
python main.py
```

This will create broadcasts for all enabled services that occur within the date range.

### Dry Run Mode

Preview what would be created without making changes:

1. Edit `.env` and set:
```
DRY_RUN=true
```

2. Run the scheduler:
```bash
python main.py
```

## Configuration Reference

### Required Settings

- `OAUTH2_CREDENTIALS_FILE`: Path to OAuth2 credentials JSON (default: `OAuth2.json`)
- `CHANNEL_ID`: YouTube channel ID
- `PLAYLIST_ID`: Playlist ID to add broadcasts to
- `CAMPUS_NAME`: Campus name for stream titles and auto-detection (e.g., "Fishers")
- `ENABLED_SERVICES`: Comma-separated list of services to schedule (e.g., "A,B,C,D,E,F")

### Service Configuration (Per Service A-H)

Each service requires the following environment variables:

- `SERVICE_X_NAME`: Display name for the service (e.g., "Saturday 4:00pm Service")
- `SERVICE_X_DAY`: Day of the week (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)
- `SERVICE_X_TIME`: Time in 24-hour format HH:MM (e.g., "16:00" for 4:00 PM)
- `SERVICE_X_DESCRIPTION`: Optional description for the broadcast (leave empty for no description)

**Note**: Services G and H can have empty DAY and TIME values for use as special event slots with date range mode. Stream keys are automatically detected based on the `CAMPUS_NAME` setting.

### Optional Settings

- `TIMEZONE`: Timezone for service times (default: `America/Indianapolis`)
- `PRIVACY_STATUS`: Broadcast privacy (`unlisted`, `private`, or `public`, default: `unlisted`)
- `START_DATE`: Start date for range mode (format: `YYYY-MM-DD`)
- `END_DATE`: End date for range mode (format: `YYYY-MM-DD`)
- `DRY_RUN`: Preview mode without creating broadcasts (`true` or `false`, default: `false`)

### Changing Service Times

To change a service time, simply update the corresponding environment variables in your `.env` file:

```env
# Change Sunday 9:30am service to 10:00am
SERVICE_D_NAME=Sunday 10:00am Service
SERVICE_D_DAY=Sunday
SERVICE_D_TIME=10:00
```

## Stream Key Auto-Detection

Stream keys are automatically detected and mapped based on the naming pattern:
```
{CAMPUS_NAME} Stream {Letter}
```

For example, with `CAMPUS_NAME=Fishers`:
- `Fishers Stream A` → Service A
- `Fishers Stream B` → Service B
- etc.

This means:
1. **No manual configuration needed** - Just name your YouTube streams correctly
2. **Portable between campuses** - Change `CAMPUS_NAME` and stream names
3. **Broadcast titles automatically use campus name** - Titles will be `{CAMPUS_NAME} // MM-DD-YYYY // HH:MM AM/PM`

## Examples

### Schedule Only Weekend Services

```env
ENABLED_SERVICES=A,B,C,D,E
```

### Schedule an Entire Month

```env
ENABLED_SERVICES=A,B,C,D,E,F
START_DATE=2025-02-01
END_DATE=2025-02-28
```

### Test Configuration

```env
ENABLED_SERVICES=A
DRY_RUN=true
```

## Troubleshooting

### Authentication Errors

- Ensure OAuth2 credentials file exists and is valid
- You may need to re-authenticate if credentials expire

### No Streams Found

- Make sure you have set up stream keys in YouTube Studio
- Check that stream keys are properly mapped in `.env`

### Wrong Times

- Verify `TIMEZONE` setting matches your location
- Check service time configurations in `.env`

## License

This tool is for internal use managing church service streams.

