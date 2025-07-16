# app.py
from flask import Flask, render_template, request, flash, redirect, url_for
import datetime

app = Flask(__name__)
# IMPORTANT: Change this to a strong, random key in a real application!
app.secret_key = 'your_super_secret_key_here_generate_a_new_one'

# Your core calculation logic, adapted to return values instead of printing/saving
def calculate_bill_details():
    last_month_reading = float(request.form['last_month_reading'])
    current_month_reading = float(request.form['current_month_reading'])

    units_consumed = current_month_reading - last_month_reading

    # Define hypothetical tariff rates for Bengaluru (illustrative and subject to change)
    # Always refer to the official BESCOM website or your bill for current rates.
    tariff_slabs = [
        (0, 50, 4.10),    # First 50 units @ Rs. 4.10/unit
        (51, 100, 5.55),  # Next 50 units (51-100) @ Rs. 5.55/unit
        (101, 200, 7.10), # Next 100 units (101-200) @ Rs. 7.10/unit
        (201, float('inf'), 8.50) # Above 200 units @ Rs. 8.50/unit
    ]

    fixed_charges_per_kw = 50.00
    sanctioned_load_kw = 1.0 # Assuming 1 kW sanctioned load for simplicity. Can be user input.

    bill_amount = 0.0
    calculation_details = []
    current_units_for_calculation = units_consumed

    for lower_bound, upper_bound, rate in tariff_slabs:
        if current_units_for_calculation <= 0:
            break

        slab_range_text = ""
        if upper_bound == float('inf'):
            slab_range_text = f"Above {lower_bound-1} units"
        else:
            slab_range_text = f"{lower_bound}-{upper_bound} units"

        units_in_this_slab = 0
        if lower_bound <= units_consumed:
            if upper_bound == float('inf'):
                units_in_this_slab = current_units_for_calculation
            else:
                # Calculate units applicable to the current slab
                if lower_bound == 0:
                    units_in_this_slab = min(current_units_for_calculation, upper_bound - lower_bound + 1)
                else:
                    units_in_this_slab = min(current_units_for_calculation, upper_bound - (lower_bound - 1))


            if units_in_this_slab > 0:
                cost_for_slab = units_in_this_slab * rate
                bill_amount += cost_for_slab
                calculation_details.append({
                    'description': f"{units_in_this_slab:.2f} units @ ₹{rate:.2f}/unit ({slab_range_text})",
                    'amount': cost_for_slab
                })
                current_units_for_calculation -= units_in_this_slab

    fixed_charge_amount = fixed_charges_per_kw * sanctioned_load_kw
    bill_amount += fixed_charge_amount
    calculation_details.append({
        'description': f"Fixed Charges ({sanctioned_load_kw:.1f} kW)",
        'amount': fixed_charge_amount
    })

    return {
        'last_month_reading': last_month_reading,
        'current_month_reading': current_month_reading,
        'units_consumed': units_consumed,
        'calculation_details': calculation_details,
        'total_amount': bill_amount,
        'current_date': datetime.date.today().strftime("%d %B %Y")
    }

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            last_month_reading_str = request.form['last_month_reading']
            current_month_reading_str = request.form['current_month_reading']

            # Basic validation for empty strings
            if not last_month_reading_str or not current_month_reading_str:
                flash("Please provide both last month's and current month's readings.", 'error')
                return redirect(url_for('index'))

            last_month_reading = float(last_month_reading_str)
            current_month_reading = float(current_month_reading_str)

            if current_month_reading < last_month_reading:
                flash("Current month's reading cannot be less than last month's reading. Please re-enter.", 'error')
                return redirect(url_for('index'))

            bill_data = calculate_bill_details() # Call the calculation function
            return render_template('index.html', bill=bill_data)

        except ValueError:
            flash("Invalid input. Please enter numerical values for meter readings.", 'error')
            return redirect(url_for('index'))
        except KeyError:
            flash("Form fields not found. Please ensure correct input names.", 'error')
            return redirect(url_for('index'))
    
    # For GET requests or initial page load
    return render_template('index.html', bill=None)

if __name__ == '__main__':
    app.run(debug=True) # debug=True is good for development, set to False for production
