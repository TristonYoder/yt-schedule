# Changelog

## Version 2.2.0 - Persistent Authentication & Per-Service Descriptions

### New Features
- **Persistent authentication** - Only authenticate once, credentials saved to `token.pickle`
- **Automatic token refresh** - Expired credentials are refreshed automatically
- **Per-service descriptions** - Each service (A-H) can have its own custom description

### Improvements
- No more repeated browser authentication on every run
- Added `token.pickle` to `.gitignore` for security

## Version 2.1.0 - Command-Line Interface & Cleanup

### New Features
- **Command-line arguments** for weeks scheduling (`-w` or `--weeks`)
- **Remove command** (`--remove` or `-rm`) to delete all scheduled broadcasts
- **Dry-run flag** (`--dry-run`) for safe preview mode
- **Campus name** now used in broadcast titles automatically

### Improvements
- Removed unused authentication methods (API key and service account)
- Simplified configuration - only OAuth2 is needed now
- Cleaner codebase with unused imports removed

### Breaking Changes
- Removed `API_KEY` and `SERVICE_ACCOUNT_FILE` from configuration (no longer needed)

## Version 2.0.0 - Configuration Refactor

### Major Changes

#### Environment-Based Configuration
- All configuration now loaded from `.env` file
- Removed hardcoded credentials and settings from code
- Added `env.example` template for easy setup
- Added `.gitignore` to protect sensitive files

#### Flexible Service Configuration
- Service schedules now fully configurable via environment variables
- Each service (A-H) can have custom:
  - Display name (e.g., "Saturday 4:00pm Service")
  - Day of week
  - Time of day
  - Stream key mapping
- Easy to change service times without modifying code

#### Enhanced Features
- **Dry Run Mode**: Preview what would be created without making actual API calls
- **Date Range Mode**: Schedule services across custom date ranges
- **Auto Mode**: Automatically calculate next occurrence (default)
- **Better Logging**: Comprehensive logging throughout the application
- **Error Handling**: Graceful handling of API errors and configuration issues
- **Configuration Validation**: Validates all required settings before running

#### Service Configuration Format

Previous approach (hardcoded):
```python
SERVICE_SCHEDULES = {
    'A': {'day': 5, 'hour': 16, 'minute': 0}
}
STREAM_KEY_A = 0
```

New approach (environment variables):
```env
SERVICE_A_NAME=Saturday 4:00pm Service
SERVICE_A_DAY=Saturday
SERVICE_A_TIME=16:00
SERVICE_A_STREAM_KEY=0
```

### Benefits

1. **Security**: API keys and credentials no longer in source code
2. **Flexibility**: Change service times without code changes
3. **Maintainability**: Clear separation of configuration and code
4. **Safety**: Dry run mode to test before creating broadcasts
5. **Clarity**: Service names make it clear what each stream is for

### Migration Guide

1. Copy `env.example` to `.env`
2. Update `.env` with your credentials and settings
3. Configure each service's name, schedule, and stream key
4. Run with `DRY_RUN=true` first to verify configuration
5. Set `DRY_RUN=false` when ready to create actual broadcasts

### Files Changed

- `main.py` - Complete refactor with new configuration system
- `requirements.txt` - Updated dependencies
- `env.example` - Configuration template
- `.gitignore` - Added to protect sensitive files
- `README.md` - Updated documentation
- `CHANGELOG.md` - This file

### Files Removed

- `requirements` (replaced by `requirements.txt`)

### Dependencies Updated

- `google-api-python-client`: 1.7.2 → 2.108.0
- `google-auth`: 1.8.0 → 2.25.2
- `google-auth-httplib2`: 0.0.3 → 0.2.0
- `google-auth-oauthlib`: 0.4.1 → 1.2.0
- Added: `python-dotenv==1.0.0`

