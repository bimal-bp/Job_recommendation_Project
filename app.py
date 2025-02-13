# Dashboard page
def dashboard(email, role):
    st.title("User Dashboard")
    st.sidebar.title("Menu")
    
    # Remove "Job Recommendations" from the sidebar menu
    menu_options = ["Profile Setup", "Market Trends"]  # Only "Profile Setup" and "Market Trends" in the sidebar
    
    choice = st.sidebar.radio("Go to", menu_options)

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    cur = conn.cursor()

    if choice == "Profile Setup":
        st.subheader("Profile Setup")

        # Fetch existing user data
        cur.execute("SELECT full_name, skills, contact, locations, experience, job_role, salary, industries, job_type FROM users WHERE email = %s", (email,))
        user_data = cur.fetchone()

        # Default values if no data exists
        full_name = user_data[0] if user_data and user_data[0] else ""
        skills = ast.literal_eval(user_data[1]) if user_data and user_data[1] else []
        contact = user_data[2] if user_data and user_data[2] else ""
        locations = ast.literal_eval(user_data[3]) if user_data and user_data[3] else []
        experience = user_data[4] if user_data and user_data[4] else 0
        job_role = user_data[5] if user_data and user_data[5] else ""
        salary = user_data[6] if user_data and user_data[6] else ""
        industries = ast.literal_eval(user_data[7]) if user_data and user_data[7] else []
        job_type = user_data[8] if user_data and user_data[8] else ""

        # Input fields
        full_name = st.text_input("Full Name", full_name)
        skills = st.text_area("Skills (comma separated)", ", ".join(skills)).split(", ")
        contact = st.text_input("Contact Information", contact)
        locations = st.multiselect("Preferred Job Locations", ["Bangalore", "Hyderabad", "Delhi", "Mumbai", "Remote"], default=locations)
        experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=experience)
        job_role = st.text_input("Job Role", job_role)
        salary = st.text_input("Expected Salary Range", salary)
        industries = st.multiselect("Interested Industries", ["IT", "Finance", "Healthcare", "Education"], default=industries)
        job_type = st.selectbox("Preferred Job Type", ["Full-time", "Part-time", "Remote", "Contract"], index=["Full-time", "Part-time", "Remote", "Contract"].index(job_type) if job_type else 0)

        # Save button
        if st.button("Save Profile"):
            try:
                cur.execute("""
                    UPDATE users SET full_name = %s, skills = %s, contact = %s, locations = %s, experience = %s, 
                    job_role = %s, salary = %s, industries = %s, job_type = %s WHERE email = %s
                """, (full_name, skills, contact, locations, experience, job_role, salary, industries, job_type, email))
                conn.commit()
                st.success("Profile updated successfully!")
            except Exception as e:
                st.error(f"Error updating profile: {e}")

        # Add "Job Recommendations" button below the "Profile Setup" section
        if st.button("Job Recommendations"):
            st.subheader("Job Recommendations")
            st.write("Coming soon...")

    elif choice == "Market Trends":
        st.subheader("Market Trends")
        
        # Fetch and display market trends
        cur.execute("SELECT trend FROM market_trends ORDER BY id DESC")  # Assuming you have a market_trends table
        trends = cur.fetchall()
        
        if trends:
            st.write("Latest Market Trends:")
            for trend in trends:
                st.write(f"- {trend[0]}")
        else:
            st.write("No market trends available.")
        
        # Allow only admins to submit new trends
        if role == "admin":
            trend_input = st.text_area("Enter Market Trends")
            if st.button("Submit Trends"):
                if trend_input:
                    try:
                        cur.execute("INSERT INTO market_trends (trend) VALUES (%s)", (trend_input,))
                        conn.commit()
                        st.success("Market trends submitted successfully!")
                    except Exception as e:
                        st.error(f"Error submitting trends: {e}")
                else:
                    st.error("Please enter some text before submitting.")

    conn.close()
