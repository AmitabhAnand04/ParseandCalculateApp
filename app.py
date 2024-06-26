import sys
import spacy
import pyodbc
from decimal import Decimal
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os

# Define connection parameters
server = 'chatbotserver456.database.windows.net'
database = 'pocdb'
username = 'sqlserver'
password = 'chatbot@123'

# Get the current directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Define the path to the model
model_path = os.path.join(current_dir, "model", "model-best")

# Load the custom spaCy model
nlp = spacy.load(model_path)

# Initialize DataNotAvailable dictionary
DataNotAvailable = {}

app = Flask(__name__)
CORS(app)

# Helper function to convert numerical strings to float after removing commas
def convert_to_float(value):
    return float(value.replace(',', '')) if ',' in value else float(value)

# Helper function to format numbers with commas and two decimal places
def format_currency(value):
    return "${:,.2f}".format(value)

# Function to fetch a single value from the database
def fetch_single_value(cursor, query, params, entity_name):
    cursor.execute(query, params)
    result = cursor.fetchone()
    if result is None:
        # Store the entity name and query parameter in DataNotAvailable
        DataNotAvailable[entity_name] = params[0]
        return None
    return float(result[0])

# Function to calculate the premium
def calculate_premium(entities):
    global DataNotAvailable
    DataNotAvailable = {}  # Reset DataNotAvailable dictionary
    description = ""  # Initialize description string

    
    
    # Create a connection to the SQL Server database
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = conn.cursor()

    # Determine industry code or description
    if 'INDUSTRY_CODE' in entities:
        base_rate = fetch_single_value(cursor, "SELECT BaseRate FROM IndustryBaseRates WHERE IndustryCode = ?", (entities['INDUSTRY_CODE'],), "INDUSTRY_CODE")
        description += f"Industry Code: {entities['INDUSTRY_CODE']}\n"
    elif 'INDUSTRY_DESC' in entities:
        base_rate = fetch_single_value(cursor, "SELECT BaseRate FROM IndustryBaseRates WHERE IndustryDescription = ?", (entities['INDUSTRY_DESC'],), "INDUSTRY_DESC")
        description += f"Industry Description: {entities['INDUSTRY_DESC']}\n"
    else:
        raise ValueError("Industry information is missing.")

    # Determine location multiplier
    if 'ZIP_CODE' in entities:
        location_multiplier = fetch_single_value(cursor, "SELECT LocationMultiplier FROM GeographicFactors WHERE ZIPCode = ?", (entities['ZIP_CODE'],), "ZIP_CODE")
        description += f"ZIP Code: {entities['ZIP_CODE']}\n"
    elif 'ADDRESS' in entities:
        location_multiplier = fetch_single_value(cursor, "SELECT LocationMultiplier FROM GeographicFactors WHERE RegionDescription = ?", (entities['ADDRESS'],), "ADDRESS")
        description += f"Address: {entities['ADDRESS']}\n"
    else:
        raise ValueError("Location information is missing.")

    annual_revenue = float(entities.get('ANNUAL_REVENUE', 0))
    square_footage = float(entities.get('SQUARE_FOOTAGE', 0))
    property_value = float(entities.get('PROPERTY_VALUE', 0))
    coverage_limit = entities.get('COVERAGE_LIMIT', 'Standard')
    deductible_amount = float(entities.get('DEDUCTIBLE_AMOUNT', 0))
    claims_history = entities.get('CLAIMS_HISTORY', 'No claims')
    risk_management = entities.get('RISK_MANAGEMENT', 'None')
    operational_hours = entities.get('OPERATIONAL_HOURS', '9 AM - 5 PM')
    employee_turnover = float(entities.get('EMPLOYEE_TURNOVER', 0))

    description += f"Property Value: {format_currency(property_value)}\n"

    # Retrieve size factors based on revenue and square footage
    revenue_size_factor = fetch_single_value(cursor, "SELECT SizeFactor FROM BusinessSizeAdjustments WHERE ? BETWEEN LowRevenue AND HighRevenue", (annual_revenue,), "ANNUAL_REVENUE")
    square_footage_size_factor = fetch_single_value(cursor, "SELECT SizeFactor FROM SquareFootageAdjustments WHERE ? BETWEEN LowSquareFootage AND HighSquareFootage", (square_footage,), "SQUARE_FOOTAGE")

    # Retrieve property value factor
    property_value_factor = fetch_single_value(cursor, "SELECT PropertyValueFactor FROM PropertyValueAdjustments WHERE ? BETWEEN LowPropertyValue AND HighPropertyValue", (property_value,), "PROPERTY_VALUE")

    # Retrieve coverage limit factor
    coverage_limit_factor = fetch_single_value(cursor, "SELECT CoverageFactor FROM CoverageLimitAdjustments WHERE CoverageLimit = ?", (coverage_limit,), "COVERAGE_LIMIT")

    # Retrieve deductible factor
    deductible_factor = fetch_single_value(cursor, "SELECT DeductibleFactor FROM DeductibleAdjustments WHERE DeductibleAmount = ?", (deductible_amount,), "DEDUCTIBLE_AMOUNT")

    # Retrieve claims history factor
    claims_history_factor = fetch_single_value(cursor, "SELECT ClaimsFactor FROM ClaimsHistoryAdjustments WHERE ClaimsHistory = ?", (claims_history,), "CLAIMS_HISTORY")

    # Retrieve risk management factor
    risk_management_factor = fetch_single_value(cursor, "SELECT Factor FROM RiskManagementPractices WHERE Practice = ?", (risk_management,), "RISK_MANAGEMENT")

    # Retrieve operational hours factor
    operational_hours_factor = fetch_single_value(cursor, "SELECT OperationalFactor FROM OperationalHours WHERE OperationalHours = ?", (operational_hours,), "OPERATIONAL_HOURS")

    # Retrieve employee turnover factor
    employee_turnover_factor = fetch_single_value(cursor, "SELECT EmployeeFactor FROM EmployeeFactors WHERE ? BETWEEN LowTurnover AND HighTurnover", (employee_turnover,), "EMPLOYEE_TURNOVER")

    if DataNotAvailable:
        return None, DataNotAvailable

    # Calculate base premium
    base_premium = base_rate * (property_value / 100000)
    description += f"Base Rate per $100,000 Property Value: {format_currency(base_rate)}\n"
    description += f"Base Premium: {format_currency(base_rate)} x ({property_value} / 100,000) = {format_currency(base_premium)}\n"

    # Apply all the multipliers to the base premium
    final_premium = base_premium * location_multiplier
    description += f"Location Multiplier: {location_multiplier}\n"
    description += f"Location Adjusted Premium: {format_currency(base_premium)} x {location_multiplier} = {format_currency(final_premium)}\n"

    final_premium *= revenue_size_factor
    description += f"Annual Revenue: {format_currency(annual_revenue)}\n"
    description += f"Size Factor: {revenue_size_factor}\n"
    final_premium *= square_footage_size_factor
    description += f"Square Footage: {square_footage}\n"
    description += f"Square Footage Factor: {square_footage_size_factor}\n"
    description += f"Size Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= property_value_factor
    description += f"Property Value Factor: {property_value_factor}\n"
    description += f"Property Value Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= coverage_limit_factor
    description += f"Coverage Limit: {coverage_limit}\n"
    description += f"Coverage Factor: {coverage_limit_factor}\n"
    description += f"Coverage Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= deductible_factor
    description += f"Deductible: {format_currency(deductible_amount)}\n"
    description += f"Deductible Factor: {deductible_factor}\n"
    description += f"Deductible Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= claims_history_factor
    description += f"Claims History: {claims_history}\n"
    description += f"Claims Factor: {claims_history_factor}\n"
    description += f"Claims Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= risk_management_factor
    description += f"Risk Management Practices: {risk_management}\n"
    description += f"Risk Management Factor: {risk_management_factor}\n"
    description += f"Risk Management Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= operational_hours_factor
    description += f"Operational Hours: {operational_hours}\n"
    description += f"Operational Hours Factor: {operational_hours_factor}\n"
    description += f"Operational Hours Adjusted Premium: {format_currency(final_premium)}\n"

    final_premium *= employee_turnover_factor
    description += f"Employee Turnover: {employee_turnover}\n"
    description += f"Employee Turnover Factor: {employee_turnover_factor}\n"
    description += f"Employee Turnover Adjusted Premium: {format_currency(final_premium)}\n"

    description += f"Final Premium: {format_currency(final_premium)}\n"

    return final_premium, description

@app.route('/')
def hello_world():
    template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hello, World!</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                font-family: Arial, sans-serif;
            }
            p {
                color: green;
                font-weight: bold;
                font-size: 24px;
            }
        </style>
    </head>
    <body>
        <div>
            <p>Hello, World! This is api testing. API is Online.</p>
        </div>
    </body>
    </html>
    '''
    return render_template_string(template)

# Database connection
def get_db_connection():
    conn = pyodbc.connect(
        f'DRIVER={{ODBC Driver 17 for SQL Server}};'
        f'SERVER={server};'
        f'DATABASE={database};'
        f'UID={username};'
        f'PWD={password}'
    )
    return conn

# Route to fetch all data
@app.route('/calculate_premium/help', methods=['GET'])
def get_all_parameters():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ParameterHelpTable')
    rows = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return jsonify(results)

# Route to fetch data for a specific parameter
@app.route('/calculate_premium/help/<parameter_name>', methods=['GET'])
def get_parameter(parameter_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ParameterHelpTable WHERE parameter LIKE ?', ('%' + parameter_name + '%',))
    row = cursor.fetchone()
    conn.close()
    if row:
        columns = [column[0] for column in cursor.description]
        result = dict(zip(columns, row))
        return jsonify(result)
    else:
        return jsonify({'error': 'Parameter not found'}), 404

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
        if 'INDUSTRY_CODE' not in entities and 'INDUSTRY_DESC' not in entities:
            missing_fields.append('Industry information')
        if 'ZIP_CODE' not in entities and 'ADDRESS' not in entities:
            missing_fields.append('Address information')
        if 'ANNUAL_REVENUE' in entities:
            entities['ANNUAL_REVENUE'] = convert_to_float(entities.get('ANNUAL_REVENUE', '0'))
        else:
            missing_fields.append('Annual Revenue')
        if 'SQUARE_FOOTAGE' in entities:
            entities['SQUARE_FOOTAGE'] = convert_to_float(entities.get('SQUARE_FOOTAGE', '0'))
        else:
            missing_fields.append('Square footage')
        if 'PROPERTY_VALUE' in entities:
            entities['PROPERTY_VALUE'] = convert_to_float(entities.get('PROPERTY_VALUE', '0'))
        else:
            missing_fields.append('Property value')
        if 'COVERAGE_LIMIT' not in entities:
            missing_fields.append('Coverage limit')
        if 'DEDUCTIBLE_AMOUNT' in entities:
            entities['DEDUCTIBLE_AMOUNT'] = convert_to_float(entities.get('DEDUCTIBLE_AMOUNT', '0'))
        else:
            missing_fields.append('Deductible amount')
        if 'CLAIMS_HISTORY' not in entities:
            missing_fields.append('Claims history')
        if 'RISK_MANAGEMENT' not in entities:
            missing_fields.append('Risk management')
        if 'OPERATIONAL_HOURS' in entities:
            operational_hours = entities.get('OPERATIONAL_HOURS', '9 AM - 5 PM')
            if 'to' in operational_hours:
                operational_hours = operational_hours.replace('to', '-')
            entities['OPERATIONAL_HOURS'] = operational_hours
        else:
            missing_fields.append('Operational hours')
        if 'EMPLOYEE_TURNOVER' in entities:
            entities['EMPLOYEE_TURNOVER'] = convert_to_float(entities.get('EMPLOYEE_TURNOVER', '0'))
        else:
            missing_fields.append('Employee turnover')
        
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

if __name__ == '__main__':
    app.run(debug=True)
