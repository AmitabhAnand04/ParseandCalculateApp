# Insurance Premium Calculator API

Welcome to the Parse and Calculate App! This application calculates insurance premiums based on various business and property factors using a custom spaCy Named Entity Recognition (NER) model and data from an SQL Server database.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)
- [License](#license)

## Installation

### Prerequisites

- Python 3.6 or higher
- SQL Server
- Required Python packages (listed in `requirements.txt`)

### Steps

1. Clone the repository:

    ```sh
    git clone https://github.com/AmitabhAnand04/ParseandCalculateApp.git
    cd ParseandCalculateApp
    ```

2. Create and activate a virtual environment:

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3. Install the required packages:

    ```sh
    pip install -r requirements.txt
    ```

4. Ensure your SQL Server is running and accessible with the correct credentials.

5. Run the Flask app:

    ```sh
    python app.py
    ```

## Usage

Once the Flask app is running, you can use an HTTP client like Postman or cURL to interact with the API.

### Example Request

To calculate the insurance premium, send a POST request to `/calculate_premium` with a plain English sentence containing the relevant business and property details.

```sh
curl -X POST -d "Our business with an industry code of 1234 is located in ZIP code 90210, has an annual revenue of $500,000, covers 2,000 square feet, has a property value of $1,000,000, a deductible amount of $10,000, no claims history, no risk management, operates from 9 AM to 5 PM, and has an employee turnover rate of 5%." http://localhost:5000/calculate_premium?showdetails=true
```

## API Endpoints

### `GET /`

Returns a simple greeting message to verify the server is running.

### `POST /calculate_premium`

Calculates the insurance premium based on the provided business and property details in plain English.

#### Parameters

- Request body should be a plain English sentence with the necessary details.
- Optional query parameter `showdetails=true` to get a detailed breakdown of the premium calculation.

#### Responses

- `200 OK` with the calculated premium and details (if requested).
- `400 Bad Request` with a message if required fields are missing or data is unavailable.

## Environment Variables

The application relies on several environment variables for configuration:

- `MODEL_PATH`: Path to the custom spaCy model.
- `DB_SERVER`: SQL Server name.
- `DB_DATABASE`: Database name.
- `DB_USERNAME`: Database username.
- `DB_PASSWORD`: Database password.

## Database Schema

The SQL Server database should contain the following tables with appropriate data for the application to function correctly:

- `IndustryBaseRates`
- `GeographicFactors`
- `BusinessSizeAdjustments`
- `SquareFootageAdjustments`
- `PropertyValueAdjustments`
- `CoverageLimitAdjustments`
- `DeductibleAdjustments`
- `ClaimsHistoryAdjustments`
- `RiskManagementPractices`
- `OperationalHours`
- `EmployeeFactors`

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to contribute by opening issues or submitting pull requests. Happy coding!

## Code Overview

The core functionality is implemented in a Flask app with the following key components:

- **spaCy NER model**: Used to extract relevant entities from the input text.
- **Database queries**: Fetch data from the SQL Server database to calculate the insurance premium.
- **Premium calculation logic**: Applies various factors and multipliers to compute the final premium.

### Key Functions

- `convert_to_float(value)`: Helper function to convert numerical strings to float after removing commas.
- `fetch_single_value(cursor, query, params, entity_name)`: Fetches a single value from the database.
- `calculate_premium(entities)`: Main function to calculate the insurance premium based on the extracted entities.
- `calculate_premium_endpoint()`: API endpoint to handle POST requests for premium calculation.

### Example Code Snippet

```python
@app.route('/calculate_premium', methods=['POST'])
def calculate_premium_endpoint():
    sample_text = request.data.decode('utf-8')
    show_details = request.args.get('showdetails', 'false').lower() == 'true'

    # Process the input text with spaCy
    doc = nlp(sample_text)
    entities = {}
    if doc.ents:
        for ent in doc.ents:
            entities[ent.label_] = ent.text
    else:
        return jsonify({"error": "No entities detected."}), 400

    # Create a list for missing fields
    missing_fields = []

    try:
        # Perform necessary conversions and validations
        # (logic omitted for brevity)

        if missing_fields:
            return jsonify({"missing_fields": missing_fields}), 400

        # Calculate the premium
        premium, description = calculate_premium(entities)
        if DataNotAvailable:
            return jsonify({"DataNotAvailableError": DataNotAvailable}), 400

        if show_details:
            return jsonify({"premium": f"${premium:.2f}", "details": description})
        else:
            return jsonify({"premium": f"${premium:.2f}"})

    except ValueError as e:
        return str(e), 400
```

For more detailed information, refer to the full code in the repository.
