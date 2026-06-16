# Nexora Edge Service

Edge service for IoT integration — minimal structure and quickstart guide.

## Requirements
- Python 3.10+ (recommended)
- Git

## Local installation and run

1. Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables

- Create a `.env` file in the project root if you use `python-dotenv`, or export variables in your environment.

4. Run the application:

```powershell
python app.py
```

## Main structure

- `app.py`: main entry point of the service ([app.py](app.py)).
- `requirements.txt`: project dependencies ([requirements.txt](requirements.txt)).
- `shared/infrastructure/database.py`: data connection initialization ([shared/infrastructure/database.py](shared/infrastructure/database.py)).
- Main modules: `iam/`, `monitoring/` and `shared/` (contain the `application`, `domain`, `infrastructure`, and `interfaces` layers).

## Development

- Formatting and linting: apply your preferred formatter and linter (Black, pylint, flake8).
- Run changes from the repository root and test endpoints/local components according to the service design.
