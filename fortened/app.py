import pandas as pd
import streamlit as st

from api import APIError, api_request, login_user, register_student


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="College Library Management System",
    page_icon="📚",
    layout="wide"
)

# =====================================================
# PROFESSIONAL COLLEGE LIBRARY UI DESIGN
# =====================================================



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');

.stApp {
    background: linear-gradient(135deg, #f0fdf4, #ecfdf5, #ffffff);
    color: #064e3b;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

.block-container {
    max-width: 1450px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #065f46 !important;
    font-weight: 800 !important;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #064e3b, #047857, #059669);
}

section[data-testid="stSidebar"] * {
    color: white !important;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 10px;
    margin: 5px 0;
}

section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.25);
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #ffffff, #d1fae5);
    border: 1px solid #a7f3d0;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 8px 25px rgba(6, 95, 70, 0.09);
}

[data-testid="stMetricValue"] {
    color: #047857 !important;
    font-weight: 800 !important;
}

.stButton > button,
.stFormSubmitButton > button {
    background: linear-gradient(100deg, #047857, #10b981);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 18px;
    font-weight: 700;
    transition: 0.3s;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: linear-gradient(100deg, #065f46, #059669);
    color: white;
    transform: translateY(-2px);
    border: none;
}

.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    border-radius: 10px;
    border: 1px solid #a7f3d0;
    background: white;
}

[data-baseweb="select"] > div {
    border-radius: 10px;
    border-color: #a7f3d0;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    background: #d1fae5;
    border-radius: 10px 10px 0 0;
    padding: 12px 18px;
    font-weight: 700;
}

.stTabs [aria-selected="true"] {
    background: #a7f3d0 !important;
    color: #064e3b !important;
}

div[data-testid="stForm"] {
    background: white;
    border: 1px solid #a7f3d0;
    border-radius: 16px;
    padding: 22px;
    box-shadow: 0 8px 22px rgba(6, 95, 70, 0.06);
}

[data-testid="stDataFrame"] {
    border-radius: 14px;
    overflow: hidden;
}

[data-testid="stAlert"] {
    border-radius: 12px;
}

hr {
    border-color: #a7f3d0;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# 2. SESSION STATE
# =====================================================

if "token" not in st.session_state:
    st.session_state.token = None

if "user" not in st.session_state:
    st.session_state.user = None


# =====================================================
# 3. COMMON HELPERS
# =====================================================

def get_role():
    if st.session_state.user:
        return st.session_state.user.get("role")
    return None


def api_call(method, endpoint, data=None, params=None):
    return api_request(
        method=method,
        endpoint=endpoint,
        token=st.session_state.token,
        data=data,
        params=params
    )


def show_error(error):
    st.error(str(error))


def show_table(records):
    if records:
        st.dataframe(
            pd.DataFrame(records),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No records found.")


def logout():
    st.session_state.token = None
    st.session_state.user = None
    st.rerun()


# =====================================================
# 4. LOGIN AND STUDENT ACCOUNT REGISTRATION
# =====================================================

def authentication_page():

    st.title("📚 College Library Management System")
    st.caption("Welcome to the College Library Portal")

    login_tab, register_tab = st.tabs(
        ["🔐 Login", "🎓 Student Account Registration"]
    )

    # LOGIN FORM
    with login_tab:

        st.subheader("Login to Your Account")

        with st.form("login_form"):

            email = st.text_input("Email Address")

            password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login_button:

            if not email or not password:
                st.warning("Please enter email and password.")

            else:
                try:
                    result = login_user(email, password)
                    token = result["access_token"]

                    user = api_request(
                        method="GET",
                        endpoint="/auth/me",
                        token=token
                    )

                    st.session_state.token = token
                    st.session_state.user = user

                    st.success("Login successful!")
                    st.rerun()

                except APIError as error:
                    show_error(error)

                except (KeyError, ValueError):
                    st.error(
                        "Unexpected login response. Check /auth/login "
                        "and /auth/me in your FastAPI backend."
                    )

    # STUDENT ACCOUNT REGISTRATION
    with register_tab:

        st.subheader("Create Student Account")

        st.info(
            "First ask the librarian to register you as a library "
            "member. Then use your Member ID and the same registered "
            "email below."
        )

        with st.form("student_registration_form"):

            member_id = st.number_input(
                "Member ID",
                min_value=1,
                step=1
            )

            email = st.text_input("Registered Member Email")

            password = st.text_input(
                "Create Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            register_button = st.form_submit_button(
                "Create Student Account",
                use_container_width=True
            )

        if register_button:

            if not email or not password:
                st.warning("Please complete all fields.")

            elif len(password) < 8:
                st.warning("Password must contain at least 8 characters.")

            elif len(password.encode("utf-8")) > 72:
                st.warning("Password must not exceed 72 bytes.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:
                try:
                    register_student(
                        email=email,
                        password=password,
                        member_id=int(member_id)
                    )

                    st.success("Student account created successfully!")
                    st.info(
                        "You can now log in using your email and password."
                    )

                except APIError as error:
                    show_error(error)


# =====================================================
# 5. DASHBOARD
# =====================================================

def dashboard_page():

    st.title("📊 Library Dashboard")

    user = st.session_state.user
    role = get_role()

    st.write(f"Welcome, **{user.get('email')}**")

    try:
        with st.spinner("Loading dashboard..."):

            books = api_call("GET", "/books/")
            active_records = api_call(
                "GET",
                "/borrowings/active"
            )

            members = []

            if role in ["admin", "librarian"]:
                members = api_call("GET", "/members/")

        total_titles = len(books)

        total_copies = sum(
            book.get("total_copies", 0)
            for book in books
        )

        available_copies = sum(
            book.get("available_copies", 0)
            for book in books
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Book Titles", total_titles)
        col2.metric("Total Copies", total_copies)
        col3.metric("Available Copies", available_copies)

        if role in ["admin", "librarian"]:
            st.metric("Total Members", len(members))

        st.divider()

        st.subheader("📚 Library Collection")
        show_table(books[:10])

        st.subheader("📖 Active Borrowings")
        st.metric(
            "Active Borrowing Records",
            len(active_records)
        )

    except APIError as error:
        show_error(error)


# =====================================================
# 6. BOOK MANAGEMENT
# =====================================================

def books_page():

    st.title("📚 Book Management")

    role = get_role()

    try:
        books = api_call("GET", "/books/")

        # SEARCH
        search = st.text_input("🔍 Search Books by Title")

        categories = sorted({
            book.get("category")
            for book in books
            if book.get("category")
        })

        selected_category = st.selectbox(
            "Filter by Category",
            ["All"] + categories
        )

        filtered = books

        if search:
            filtered = [
                book for book in filtered
                if search.lower() in book.get("title", "").lower()
            ]

        if selected_category != "All":
            filtered = [
                book for book in filtered
                if book.get("category") == selected_category
            ]

        st.subheader("Library Collection")
        show_table(filtered)

        st.divider()

        # ADD BOOK: ADMIN AND LIBRARIAN
        if role in ["admin", "librarian"]:

            with st.expander("➕ Add New Book"):

                with st.form("add_book_form"):

                    title = st.text_input("Book Title")
                    author = st.text_input("Author")
                    category = st.text_input("Category")

                    total_copies = st.number_input(
                        "Total Copies",
                        min_value=1,
                        step=1
                    )

                    add_button = st.form_submit_button("Add Book")

                if add_button:

                    if not title.strip() or not author.strip():
                        st.warning("Title and author are required.")

                    else:
                        try:
                            api_call(
                                "POST",
                                "/books/",
                                data={
                                    "title": title.strip(),
                                    "author": author.strip(),
                                    "category": category.strip() or None,
                                    "total_copies": int(total_copies)
                                }
                            )

                            st.success("Book added successfully!")
                            st.rerun()

                        except APIError as error:
                            show_error(error)

        # UPDATE BOOK: ADMIN AND LIBRARIAN
        if role in ["admin", "librarian"] and books:

            with st.expander("✏️ Update Book"):

                book_options = {
                    f"{b['id']} - {b['title']}": b
                    for b in books
                }

                selected = st.selectbox(
                    "Select Book",
                    list(book_options.keys()),
                    key="update_book_select"
                )

                book = book_options[selected]

                with st.form("update_book_form"):

                    new_title = st.text_input(
                        "Title",
                        value=book.get("title", "")
                    )

                    new_author = st.text_input(
                        "Author",
                        value=book.get("author", "")
                    )

                    new_category = st.text_input(
                        "Category",
                        value=book.get("category") or ""
                    )

                    new_total = st.number_input(
                        "Total Copies",
                        min_value=1,
                        value=int(book.get("total_copies", 1)),
                        step=1
                    )

                    update_button = st.form_submit_button("Update Book")

                if update_button:

                    try:
                        api_call(
                            "PUT",
                            f"/books/{book['id']}",
                            data={
                                "title": new_title.strip(),
                                "author": new_author.strip(),
                                "category": new_category.strip() or None,
                                "total_copies": int(new_total)
                            }
                        )

                        st.success("Book updated successfully!")
                        st.rerun()

                    except APIError as error:
                        show_error(error)

        # DELETE BOOK: ADMIN ONLY
        if role == "admin" and books:

            with st.expander("🗑️ Delete Book"):

                delete_options = {
                    f"{b['id']} - {b['title']}": b["id"]
                    for b in books
                }

                selected_delete = st.selectbox(
                    "Select Book to Delete",
                    list(delete_options.keys()),
                    key="delete_book_select"
                )

                confirmed = st.checkbox("Confirm book deletion")

                if st.button("Delete Book"):

                    if not confirmed:
                        st.warning("Please confirm before deleting.")

                    else:
                        try:
                            api_call(
                                "DELETE",
                                f"/books/{delete_options[selected_delete]}"
                            )

                            st.success("Book deleted successfully!")
                            st.rerun()

                        except APIError as error:
                            show_error(error)

    except APIError as error:
        show_error(error)


# =====================================================
# 7. MEMBER MANAGEMENT
# =====================================================


def members_page():

    st.title("👥 Library Member Management")

    role = get_role()

    if role not in ["admin", "librarian"]:
        st.error("You do not have permission to manage members.")
        return

    # Fetch members
    try:
        members = api_call("GET", "/members/")
    except APIError as error:
        show_error(error)
        return

    # Convert member data into a dictionary for easy lookup
    members_by_id = {int(member["id"]): member for member in members}

    # --------------------------------------------------
    # TABS
    # --------------------------------------------------

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Register Member",
        "🔍 Search Members",
        "✏️ Update Member",
        "🗑️ Delete Member"
    ])

    # ==================================================
    # 1. REGISTER MEMBER
    # ==================================================

    with tab1:

        st.subheader("Register New Library Member")

        st.info(
            "Register the student first. Give the generated "
            "Member ID and registered email to the student."
        )

        with st.form("member_registration_form"):

            name = st.text_input("Student Full Name")
            email = st.text_input("Student Email Address")
            phone = st.text_input("Phone Number")

            register = st.form_submit_button(
                "Register Member",
                use_container_width=True
            )

        if register:

            if not name.strip() or not email.strip():
                st.warning("Please enter the student name and email.")

            else:
                try:
                    result = api_call(
                        "POST",
                        "/members/",
                        data={
                            "name": name.strip(),
                            "email": email.strip().lower(),
                            "phone": phone.strip() or None
                        }
                    )

                    st.success("Member registered successfully!")

                    st.metric("Generated Member ID", result["id"])
                    st.write("**Name:**", result["name"])
                    st.write("**Email:**", result["email"])

                    st.info(
                        "Share this Member ID and email with the student "
                        "for student account registration."
                    )

                    st.rerun()

                except APIError as error:
                    show_error(error)

    # ==================================================
    # 2. SEARCH MEMBERS
    # ==================================================

    with tab2:

        st.subheader("Search Registered Members")

        search_type = st.selectbox(
            "Search By",
            ["Member ID", "Name", "Email"]
        )

        search_value = st.text_input(
            "Enter search value"
        )

        if st.button("Search Member", use_container_width=True):

            if not search_value.strip():
                st.warning("Please enter a search value.")

            else:

                results = []

                for member in members:

                    if search_type == "Member ID":
                        if search_value.strip().isdigit():
                            if int(member["id"]) == int(search_value):
                                results.append(member)

                    elif search_type == "Name":
                        if search_value.lower() in member["name"].lower():
                            results.append(member)

                    elif search_type == "Email":
                        if search_value.lower() in member["email"].lower():
                            results.append(member)

                if results:
                    st.success(f"{len(results)} member(s) found.")
                    show_table(results)
                else:
                    st.warning("No matching members found.")

        st.divider()

        st.subheader("All Registered Members")
        show_table(members)

    # ==================================================
    # 3. UPDATE MEMBER
    # ==================================================

    with tab3:

        st.subheader("Update Member Details")

        if not members:
            st.info("No members available to update.")

        else:

            member_ids = sorted(members_by_id.keys())

            selected_id = st.selectbox(
                "Select Member ID",
                member_ids,
                key="update_member_id"
            )

            selected_member = members_by_id[selected_id]

            st.write("**Current Member Details**")
            st.write("Name:", selected_member["name"])
            st.write("Email:", selected_member["email"])
            st.write("Phone:", selected_member.get("phone") or "Not provided")

            with st.form("update_member_form"):

                new_name = st.text_input(
                    "Update Name",
                    value=selected_member["name"]
                )

                new_email = st.text_input(
                    "Update Email",
                    value=selected_member["email"]
                )

                new_phone = st.text_input(
                    "Update Phone",
                    value=selected_member.get("phone") or ""
                )

                update_button = st.form_submit_button(
                    "Update Member",
                    use_container_width=True
                )

            if update_button:

                if not new_name.strip() or not new_email.strip():
                    st.warning("Name and email cannot be empty.")

                else:
                    try:
                        result = api_call(
                            "PUT",
                            f"/members/{selected_id}",
                            data={
                                "name": new_name.strip(),
                                "email": new_email.strip().lower(),
                                "phone": new_phone.strip() or None
                            }
                        )

                        st.success("Member details updated successfully!")
                        st.json(result)
                        st.rerun()

                    except APIError as error:
                        show_error(error)

    # ==================================================
    # 4. DELETE MEMBER
    # ==================================================

    with tab4:

        st.subheader("Delete Library Member")

        if role != "admin":

            st.warning(
                "Only administrators can delete library members."
            )

        elif not members:

            st.info("No members available to delete.")

        else:

            member_ids = sorted(members_by_id.keys())

            selected_id = st.selectbox(
                "Select Member ID to Delete",
                member_ids,
                key="delete_member_id"
            )

            selected_member = members_by_id[selected_id]

            st.write("**Selected Member**")
            st.write("Member ID:", selected_member["id"])
            st.write("Name:", selected_member["name"])
            st.write("Email:", selected_member["email"])

            st.warning(
                "Deleting a member cannot be undone. "
                "Members with borrowing history cannot be deleted."
            )

            confirm_delete = st.checkbox(
                "I confirm that I want to delete this member."
            )

            if st.button(
                "Delete Member",
                type="primary",
                use_container_width=True
            ):

                if not confirm_delete:
                    st.warning("Please confirm before deleting.")

                else:
                    try:
                        result = api_call(
                            "DELETE",
                            f"/members/{selected_id}"
                        )

                        st.success(
                            result.get(
                                "message",
                                "Member deleted successfully."
                            )
                        )

                        st.rerun()

                    except APIError as error:
                        show_error(error)


# =====================================================
# 8. ADMIN: CREATE ADMIN AND LIBRARIAN ACCOUNTS
# =====================================================

def staff_accounts_page():

    st.title("👨‍💼 Staff Account Management")

    if get_role() != "admin":
        st.error("Only administrators can create staff accounts.")
        return

    st.info(
        "Create additional administrator or librarian login accounts. "
        "Students and librarians cannot access this operation."
    )

    with st.form("create_staff_form"):

        email = st.text_input("Staff Email Address")

        password = st.text_input(
            "Temporary Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        role = st.selectbox(
            "Account Role",
            ["librarian", "admin"]
        )

        submit = st.form_submit_button(
            "Create Staff Account",
            use_container_width=True
        )

    if submit:

        if not email.strip() or not password:
            st.warning("Email and password are required.")

        elif len(password) < 8:
            st.warning("Password must contain at least 8 characters.")

        elif len(password.encode("utf-8")) > 72:
            st.warning("Password must not exceed 72 bytes.")

        elif password != confirm_password:
            st.error("Passwords do not match.")

        else:
            try:
                result = api_call(
                    "POST",
                    "/auth/admin/create-user",
                    data={
                        "email": email.strip().lower(),
                        "password": password,
                        "role": role
                    }
                )

                st.success("Staff account created successfully!")

                st.write("**Account ID:**", result.get("id"))
                st.write("**Email:**", result.get("email"))
                st.write("**Role:**", result.get("role"))

                st.info(
                    "Share the login details securely with the staff "
                    "member. Do not display or store the password "
                    "in the application."
                )

            except APIError as error:
                show_error(error)


# =====================================================
# 9. BORROW BOOK
# =====================================================

def borrow_page():

    st.title("📖 Borrow Books")

    if get_role() != "student":
        st.warning("Only students can borrow books.")
        return

    try:
        books = api_call("GET", "/books/")

        available_books = [
            book for book in books
            if book.get("available_copies", 0) > 0
        ]

        if not available_books:
            st.info("No books are currently available.")
            return

        options = {
            f"{b['id']} - {b['title']} "
            f"({b['available_copies']} available)": b
            for b in available_books
        }

        with st.form("borrow_book_form"):

            selected = st.selectbox(
                "Select a Book",
                list(options.keys())
            )

            submit = st.form_submit_button(
                "Borrow Book",
                use_container_width=True
            )

        if submit:

            selected_book = options[selected]

            result = api_call(
                "POST",
                "/borrowings/borrow",
                data={
                    "book_id": selected_book["id"]
                }
            )

            st.success(
                f"Successfully borrowed: {selected_book['title']}"
            )

            st.write(
                "Borrowing Record ID:",
                result.get("id")
            )

            st.rerun()

    except APIError as error:
        show_error(error)


# =====================================================
# 10. RETURN BOOK
# =====================================================

def return_page():

    st.title("📕 Return Books")

    try:
        active_records = api_call(
            "GET",
            "/borrowings/active"
        )

        if not active_records:
            st.info("No active borrowing records.")
            return

        st.subheader("Active Borrowing Records")
        show_table(active_records)

        options = {
            f"Record {r['id']} - Book ID {r['book_id']}": r
            for r in active_records
        }

        with st.form("return_book_form"):

            selected = st.selectbox(
                "Select Borrowing Record",
                list(options.keys())
            )

            submit = st.form_submit_button(
                "Return Book",
                use_container_width=True
            )

        if submit:

            record = options[selected]

            api_call(
                "PUT",
                f"/borrowings/{record['id']}/return"
            )

            st.success("Book returned successfully!")
            st.rerun()

    except APIError as error:
        show_error(error)


# =====================================================
# 11. MAIN APPLICATION AND ROLE-BASED NAVIGATION
# =====================================================

def main():

    # Show login page when user is not logged in
    if not st.session_state.token:
        authentication_page()
        return

    user = st.session_state.user
    role = get_role()

    if not user or role not in ["admin", "librarian", "student"]:
        st.error("Invalid user session. Please log in again.")
        logout()
        return

    # SIDEBAR
    st.sidebar.title("📚 College Library")

    st.sidebar.write(f"**{user.get('email')}**")
    st.sidebar.caption(f"Role: {role.upper()}")

    st.sidebar.divider()

    # ROLE-BASED NAVIGATION
    pages = [
        "Dashboard",
        "Books"
    ]

    if role in ["admin", "librarian"]:
        pages.append("Members")

    if role == "admin":
        pages.append("Staff Accounts")

    if role == "student":
        pages.append("Borrow Books")

    pages.append("Return Books")

    selected_page = st.sidebar.radio(
        "Navigation",
        pages
    )

    st.sidebar.divider()

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):
        logout()

    # PAGE ROUTING
    if selected_page == "Dashboard":
        dashboard_page()

    elif selected_page == "Books":
        books_page()

    elif selected_page == "Members":
        members_page()

    elif selected_page == "Staff Accounts":
        staff_accounts_page()

    elif selected_page == "Borrow Books":
        borrow_page()

    elif selected_page == "Return Books":
        return_page()


# =====================================================
# 12. RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    main()