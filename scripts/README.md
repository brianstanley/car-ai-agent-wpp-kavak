# Car Embedding Scripts

This directory contains scripts for generating and managing car embeddings in the database.

## Scripts

### 1. `generate_car_embeddings.py`

Generates embeddings for car data from the CSV file and saves them to the `cars` table in the database.

**Features:**
- Reads car data from `sample_caso_ai_engineer.csv`
- Creates comprehensive descriptions for each car
- Generates embeddings using OpenAI's `text-embedding-3-small` model
- Saves all data including embeddings to the database
- Provides progress tracking and detailed reporting

**Usage:**
```bash
python scripts/generate_car_embeddings.py
```

**Requirements:**
- `OPENAI_API_KEY` environment variable
- `DATABASE_URL` environment variable
- `sample_caso_ai_engineer.csv` file in the root directory
- Required Python packages: `pandas`, `tqdm`, `openai`, `sqlalchemy`

### 2. `test_car_embeddings.py`

Test script to verify that the car embedding functionality is working correctly.

**Tests:**
- Environment variables validation
- CSV file existence and structure
- Database connection and cars table
- Existing car data and embeddings

**Usage:**
```bash
python scripts/test_car_embeddings.py
```

### 3. `check_db.py`

General database connectivity and structure checker.

**Usage:**
```bash
python scripts/check_db.py
```

## Setup Instructions

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables:**
   Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   DATABASE_URL=postgresql://user:password@host:port/database
   ```

3. **Prepare CSV File:**
   Ensure `sample_caso_ai_engineer.csv` is in the root directory with the following columns:
   - `stock_id`: Unique identifier for the car
   - `km`: Kilometers driven
   - `price`: Price in currency
   - `make`: Car manufacturer
   - `model`: Car model
   - `year`: Manufacturing year
   - `version`: Car version/trim
   - `bluetooth`: Bluetooth availability (Sí/No)
   - `largo`: Length in meters
   - `ancho`: Width in meters
   - `altura`: Height in meters
   - `car_play`: CarPlay availability (Sí/No)

4. **Run Tests:**
   ```bash
   python scripts/test_car_embeddings.py
   ```

5. **Generate Embeddings:**
   ```bash
   python scripts/generate_car_embeddings.py
   ```

## Database Schema

The `cars` table has the following structure:

```sql
CREATE TABLE cars (
    id SERIAL PRIMARY KEY,
    stock_id TEXT,
    km INT,
    price NUMERIC,
    make TEXT,
    model TEXT,
    year INT,
    version TEXT,
    bluetooth BOOLEAN,
    largo NUMERIC,
    ancho NUMERIC,
    altura NUMERIC,
    car_play BOOLEAN,
    descripcion TEXT,
    embedding VECTOR(1536)
);
```

## Car Description Format

The script generates descriptions in the following format:
```
{make} {model} {year}, versión {version}, {km:,} km, ${price:,.0f}, {bluetooth_status}, {car_play_status}, {dimensions}
```

Example:
```
Toyota Corolla 2020, versión 1.8 LE AUTO, 29,377 km, $313,999, con bluetooth, con CarPlay, 4.65m de largo, 1.78m de ancho, 1.48m de alto
```

## Error Handling

The scripts include comprehensive error handling for:
- Missing environment variables
- Database connection issues
- CSV file reading errors
- OpenAI API errors
- Data validation issues

## Performance

- Uses `tqdm` for progress tracking
- Processes cars one by one to avoid memory issues
- Provides detailed success/failure reporting
- Includes rollback on database errors

## Troubleshooting

1. **Pandas Import Error:** Ensure pandas is installed: `pip install pandas`
2. **Database Connection Error:** Check your `DATABASE_URL` in `.env`
3. **OpenAI API Error:** Verify your `OPENAI_API_KEY` is valid
4. **CSV File Error:** Ensure the CSV file exists and has the correct format 