import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import calendar

# Updated UK immunisation schedule
UK_SCHEDULE = {
    "DTaP/IPV/Hib/HepB (6-in-1)": [
        {"dose": 1, "age_weeks": 8, "min_interval": 0, "max_interval": 12},
        {"dose": 2, "age_weeks": 12, "min_interval": 4, "max_interval": 16},
        {"dose": 3, "age_weeks": 16, "min_interval": 4, "max_interval": 24}
    ],
    "PCV (Pneumococcal)": [
        {"dose": 1, "age_weeks": 12, "min_interval": 0, "max_interval": 16},
        {"dose": 2, "age_weeks": 52, "min_interval": 40, "max_interval": 60}
    ],
    "Rotavirus": [
        {"dose": 1, "age_weeks": 8, "min_interval": 0, "max_interval": 15},
        {"dose": 2, "age_weeks": 12, "min_interval": 4, "max_interval": 24}
    ],
    "MenB": [
        {"dose": 1, "age_weeks": 8, "min_interval": 0, "max_interval": 12},
        {"dose": 2, "age_weeks": 16, "min_interval": 8, "max_interval": 24},
        {"dose": 3, "age_weeks": 52, "min_interval": 36, "max_interval": 60}
    ],
    "Hib/MenC": [
        {"dose": 1, "age_weeks": 52, "min_interval": 0, "max_interval": 60}
    ],
    "MMR": [
        {"dose": 1, "age_weeks": 52, "min_interval": 0, "max_interval": 60},
        {"dose": 2, "age_weeks": 156, "min_interval": 104, "max_interval": 208}
    ],
    "DTaP/IPV (4-in-1 pre-school booster)": [
        {"dose": 1, "age_weeks": 156, "min_interval": 52, "max_interval": 208}
    ],
    "Td/IPV (Teenage booster)": [
        {"dose": 1, "age_weeks": 702, "min_interval": 0, "max_interval": 780}  # 13-14 years
    ],
    "MenACWY": [
        {"dose": 1, "age_weeks": 702, "min_interval": 0, "max_interval": 780}  # 13-14 years
    ]
}

VACCINE_INFO = {
    "DTaP/IPV/Hib/HepB (6-in-1)": "Protects against diphtheria, tetanus, pertussis, polio, Haemophilus influenzae type b and hepatitis B.",
    "PCV (Pneumococcal)": "Protects against pneumococcal infections.",
    "Rotavirus": "Protects against rotavirus infection, a common cause of childhood diarrhea.",
    "MenB": "Protects against meningococcal group B bacteria, a major cause of meningitis and septicemia.",
    "Hib/MenC": "Protects against Haemophilus influenzae type b and meningococcal group C bacteria.",
    "MMR": "Protects against measles, mumps, and rubella.",
    "DTaP/IPV (4-in-1 pre-school booster)": "Booster for diphtheria, tetanus, pertussis, and polio.",
    "Td/IPV (Teenage booster)": "Teenage booster for tetanus, diphtheria, and polio.",
    "MenACWY": "Protects against meningococcal groups A, C, W, and Y."
}

def format_date(d):
    return d.strftime("%d/%m/%Y") if d else None

def parse_date(date_string):
    try:
        return datetime.strptime(date_string, "%d/%m/%Y").date()
    except ValueError:
        return None

def calculate_age(dob):
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    weeks = (today - dob).days // 7
    return age, weeks

def calculate_years_months(from_date, to_date):
    years = to_date.year - from_date.year
    months = to_date.month - from_date.month

    if to_date.day < from_date.day:
        months -= 1

    if months < 0:
        years -= 1
        months += 12

    return years, months

def check_vaccinations(dob, vaccinations):
    today = date.today()
    results = []
    overdue_doses = {}

    for vaccine, schedule in UK_SCHEDULE.items():
        given_dates = vaccinations.get(vaccine, [])
        prev_dose_date = None
        for dose in schedule:
            if len(given_dates) >= dose['dose']:
                given_date = given_dates[dose['dose'] - 1]
                if given_date:
                    given_age_weeks = (given_date - dob).days // 7
                    status = "correct"
                    messages = []

                    # Special handling for Rotavirus
                    if vaccine == "Rotavirus":
                        if dose['dose'] == 1 and given_age_weeks >= 15:
                            status = "late"
                            messages.append(f"First dose given at {given_age_weeks} weeks. Should be given before 15 weeks.")
                        elif dose['dose'] == 2 and given_age_weeks >= 24:
                            status = "late"
                            messages.append(f"Second dose given at {given_age_weeks} weeks. Should be given before 24 weeks.")

                    # Check if vaccine was given at the right time
                    if given_age_weeks < dose['age_weeks']:
                        status = "early"
                        years, months = calculate_years_months(given_date, dob + timedelta(weeks=dose['age_weeks']))
                        if years > 0:
                            messages.append(f"Given {years} year{'s' if years != 1 else ''} and {months} month{'s' if months != 1 else ''} early")
                        else:
                            messages.append(f"Given {months} month{'s' if months != 1 else ''} early")
                    elif given_age_weeks > dose['max_interval']:
                        status = "late"
                        years, months = calculate_years_months(dob + timedelta(weeks=dose['age_weeks']), given_date)
                        if years > 0:
                            messages.append(f"Given {years} year{'s' if years != 1 else ''} and {months} month{'s' if months != 1 else ''} late")
                        else:
                            messages.append(f"Given {months} month{'s' if months != 1 else ''} late")
                    
                    # Check interval from previous dose
                    if prev_dose_date:
                        weeks_since_prev = (given_date - prev_dose_date).days // 7
                        if weeks_since_prev < dose['min_interval']:
                            status = "early"
                            messages.append(f"Interval too short: {weeks_since_prev} weeks (min {dose['min_interval']})")
                    
                    # Special handling for DTaP/IPV
                    if vaccine == "DTaP/IPV (4-in-1 pre-school booster)":
                        dtap_ipv_hib_hepb_doses = vaccinations.get("DTaP/IPV/Hib/HepB (6-in-1)", [])
                        if len(dtap_ipv_hib_hepb_doses) >= 3 and dtap_ipv_hib_hepb_doses[2]:
                            weeks_since_last_dtap = (given_date - dtap_ipv_hib_hepb_doses[2]).days // 7
                            if weeks_since_last_dtap < 52:
                                status = "early"
                                messages.append(f"Given only {weeks_since_last_dtap} weeks after the third dose of DTaP/IPV/Hib/HepB. Should be at least 1 year.")

                    message = f"Dose {dose['dose']} given at {given_age_weeks} weeks. "
                    if messages:
                        message += " ".join(messages)
                    else:
                        message += "Timing correct."

                    results.append({
                        "vaccine": vaccine,
                        "dose": dose['dose'],
                        "status": status,
                        "message": message
                    })

                    prev_dose_date = given_date
                else:
                    if (dob + timedelta(weeks=dose['age_weeks'])) <= today:
                        years, months = calculate_years_months(dob + timedelta(weeks=dose['age_weeks']), today)
                        if vaccine not in overdue_doses:
                            overdue_doses[vaccine] = []
                        overdue_doses[vaccine].append({
                            "dose": dose['dose'],
                            "years": years,
                            "months": months,
                            "min_interval": dose['min_interval']
                        })
                    else:
                        results.append({
                            "vaccine": vaccine,
                            "dose": dose['dose'],
                            "status": "due",
                            "message": f"Dose {dose['dose']} is due at {dose['age_weeks']} weeks old"
                        })
            else:
                if (dob + timedelta(weeks=dose['age_weeks'])) <= today:
                    years, months = calculate_years_months(dob + timedelta(weeks=dose['age_weeks']), today)
                    if vaccine not in overdue_doses:
                        overdue_doses[vaccine] = []
                    overdue_doses[vaccine].append({
                        "dose": dose['dose'],
                        "years": years,
                        "months": months,
                        "min_interval": dose['min_interval']
                    })
                else:
                    results.append({
                        "vaccine": vaccine,
                        "dose": dose['dose'],
                        "status": "due",
                        "message": f"Dose {dose['dose']} is due at {dose['age_weeks']} weeks old"
                    })

    # Process overdue doses
    for vaccine, doses in overdue_doses.items():
        for i, dose in enumerate(doses):
            if i == 0:
                message = f"Dose {dose['dose']} is overdue by {dose['years']} year{'s' if dose['years'] != 1 else ''} and {dose['months']} month{'s' if dose['months'] != 1 else ''}. Should be given immediately."
            else:
                message = f"Dose {dose['dose']} is overdue. Should be given {dose['min_interval']} weeks after the previous dose."
            
            results.append({
                "vaccine": vaccine,
                "dose": dose['dose'],
                "status": "overdue",
                "message": message
            })

    return results

st.set_page_config(page_title="UK Child Vaccination Checker", layout="wide")

st.title("UK Child Vaccination Checker")

st.markdown("""
    This app helps you check your child's vaccination status based on the UK immunisation schedule.
    Please enter your child's date of birth and the dates of any vaccinations they have received.
""")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Child Information")
    min_date = date.today() - timedelta(days=365*20)  # Allow birthdates up to 20 years ago
    dob_input = st.date_input("Enter the child's date of birth", 
                              min_value=min_date, 
                              max_value=date.today(),
                              help="Select the date from the calendar",
                              format="DD/MM/YYYY")
    
    if dob_input:
        dob = dob_input
        if dob > date.today():
            st.error("Date of birth cannot be in the future.")
        else:
            age_years, age_weeks = calculate_age(dob)
            st.info(f"Child's age: {age_years} years ({age_weeks} weeks)")

with col2:
    st.subheader("Vaccination Information")
    st.markdown("Select the dates for each vaccine dose received:")

vaccinations = {}
if dob:
    for vaccine in UK_SCHEDULE.keys():
        with st.expander(f"{vaccine} - {VACCINE_INFO[vaccine]}"):
            for dose in range(1, len(UK_SCHEDULE[vaccine]) + 1):
                date_input = st.date_input(
                    f"{vaccine} - Dose {dose}",
                    key=f"{vaccine}_{dose}",
                    help=f"Select the date when dose {dose} was given",
                    min_value=dob,
                    max_value=date.today(),
                    value=None,  # No default date
                    format="DD/MM/YYYY"
                )
                if date_input:
                    if date_input < dob:
                        st.error("Vaccination date cannot be before the date of birth.")
                    elif date_input > date.today():
                        st.error("Vaccination date cannot be in the future.")
                    else:
                        if vaccine not in vaccinations:
                            vaccinations[vaccine] = []
                        vaccinations[vaccine].append(date_input)
                else:
                    if vaccine not in vaccinations:
                        vaccinations[vaccine] = []
                    vaccinations[vaccine].append(None)

if st.button("Check Vaccinations", type="primary"):
    if dob and vaccinations:
        results = check_vaccinations(dob, vaccinations)
        
        st.subheader("Vaccination Status")
        
        # Create a DataFrame for better display
        df = pd.DataFrame(results)
        
        # Display overdue vaccinations
        overdue = df[df['status'] == 'overdue']
        if not overdue.empty:
            st.error("Overdue Vaccinations")
            for _, row in overdue.iterrows():
                st.warning(f"{row['vaccine']} - {row['message']}")
        
        # Display upcoming vaccinations
        upcoming = df[df['status'] == 'due']
        if not upcoming.empty:
            st.info("Upcoming Vaccinations")
            for _, row in upcoming.iterrows():
                st.info(f"{row['vaccine']} - {row['message']}")
        
        # Display correct, early, and late vaccinations
        others = df[df['status'].isin(['correct', 'early', 'late'])]
        if not others.empty:
            st.success("Completed Vaccinations")
            for _, row in others.iterrows():
                if row['status'] == 'correct':
                    st.success(f"{row['vaccine']} - {row['message']}")
                elif row['status'] == 'early':
                    st.warning(f"{row['vaccine']} - {row['message']}")
                else:
                    st.error(f"{row['vaccine']} - {row['message']}")

        # General advice
        st.subheader("General Advice")
        st.markdown("""
            - Always consult with your healthcare provider for personalized advice.
            - Catch-up on any missed vaccinations as soon as possible.
            - Keep your vaccination records up to date.
            - Visit the [NHS Vaccinations](https://www.nhs.uk/conditions/vaccinations/) page for more information.
        """)
    else:
        st.error("Please enter the child's date of birth and vaccination dates before checking.")
