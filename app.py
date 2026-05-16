"""
DYNAMIC ENGAGEMENT LETTER GENERATOR - CLOUD VERSION
Streamlit Cloud Hosted Application with GitHub Integration
Version: 3.0 (Cloud-Ready, Remote Accessible, GitHub-Backed Storage)

Hosted on Streamlit Cloud → Accessible to remote staff via web link
Letters stored in private GitHub repo → Accessible everywhere
"""

import streamlit as st
from datetime import datetime
from jinja2 import Template
import json
from pathlib import Path
import base64
import os
from io import BytesIO

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Engagement Letter Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .header-main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-card {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-card {
        background: #cfe2ff;
        border-left: 4px solid #0d6efd;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# GITHUB INTEGRATION
# ============================================================================

@st.cache_resource
def get_github_client():
    """Initialize GitHub API client using PyGithub"""
    try:
        from github import Github
        token = st.secrets.get("github_token")
        if not token:
            st.error("❌ GitHub token not found in Streamlit secrets. Configure in Settings → Secrets.")
            return None
        return Github(token)
    except ImportError:
        st.error("❌ PyGithub not installed. This shouldn't happen in Streamlit Cloud.")
        return None
    except Exception as e:
        st.error(f"❌ GitHub connection error: {str(e)}")
        return None

def fetch_master_template():
    """Fetch master engagement letter template from GitHub"""
    try:
        g = get_github_client()
        if not g:
            return get_default_template()

        repo_name = st.secrets.get("github_repo", "")
        if not repo_name:
            st.warning("⚠️ GitHub repo not configured. Using default template.")
            return get_default_template()

        try:
            # Parse owner/repo from format: "username/repo-name"
            owner, repo = repo_name.split("/")
            repo_obj = g.get_user(owner).get_repo(repo)

            # Try to fetch template
            try:
                content = repo_obj.get_contents("templates/master_engagement_letter.md")
                return content.decoded_content.decode('utf-8')
            except:
                # If file doesn't exist, return default
                return get_default_template()

        except Exception as e:
            st.warning(f"⚠️ Could not fetch template from GitHub: {str(e)}")
            return get_default_template()

    except Exception as e:
        st.warning(f"⚠️ Error: {str(e)}")
        return get_default_template()

def get_default_template():
    """Default template (fallback)"""
    return """# ENGAGEMENT LETTER

**Date**: {{GENERATED_DATE}}

**To**: {{CLIENT_NAME}}
**PAN**: {{CLIENT_PAN}}
**From**: {{FIRM_NAME}}
**Prepared by**: {{CREATED_BY}} ({{ROLE}})

---

## 1. SCOPE OF WORK

We are pleased to confirm our engagement to provide the following services:

**Service Type**: {{SERVICE_TYPE}}

**Service Description**:
{{SERVICE_DESCRIPTION}}

### Key Deliverables
- {{DELIVERABLE_1}}
- {{DELIVERABLE_2}}
- {{DELIVERABLE_3}}

---

## 2. TIMELINE & MILESTONES

| Phase | Duration | Responsibility |
|-------|----------|-----------------|
| Kickoff & Data Collection | Week 1 | {{FIRM_NAME}} & Client |
| Analysis & Review | Weeks 2–{{INTERIM_WEEK}} | {{FIRM_NAME}} |
| Final Delivery | Week {{FINAL_WEEK}} | {{FIRM_NAME}} |

**Total Timeline**: {{TIMELINE}}

---

## 3. PROFESSIONAL FEES

**Service Fee**: ₹{{FEE}}

**Payment Terms**: {{FEE_TERMS}}

**Reimbursable Expenses**: Travel, courier, printing, statutory filing fees @ cost (shall be billed separately)

---

## 4. STANDARDS & COMPLIANCE

Our work will comply with:
- {{STANDARDS_1}}
- {{STANDARDS_2}}
- Applicable Indian tax laws and regulations
- Code of Ethics issued by the Institute of Chartered Accountants of India (ICAI)

---

## 5. CONFIDENTIALITY & DATA PROTECTION

We shall maintain strict confidentiality of all client information in accordance with:
- The Chartered Accountants Act, 1949
- The Information Technology Act, 2000
- Applicable data protection regulations

**Client Data Security**:
- All client documents shall be stored securely
- Access restricted to authorized personnel only
- Documents destroyed after statutory retention period (as per applicable law)

---

## 6. RESPONSIBILITIES

**Our Responsibilities**:
- Perform services with due professional care
- Maintain independence and objectivity
- Communicate findings and recommendations clearly

**Client Responsibilities**:
- Provide timely access to books, records, and information
- Provide written representations as required
- Facilitate staff cooperation and timely responses
- Maintain internal controls over financial reporting

---

## 7. LIMITATION OF LIABILITY

Our liability under this engagement shall be limited to the fees paid for services rendered in this engagement.

---

## 8. TERMINATION

Either party may terminate this engagement with 10 business days' written notice. All outstanding fees and expenses shall be billed and payable upon termination.

---

## 9. ACCEPTANCE

We look forward to serving you and building a long-term professional relationship.

**Please confirm your acceptance** by signing below and returning one copy to us.

---

### Client Acceptance & Authorization

By signing below, you confirm that you have read and accepted the terms of this engagement letter.

**For the Client**:

Signature: _____________________________

Name: _____________________________

Designation: _____________________________

Date: _____________________________

---

**For {{FIRM_NAME}}**:

Signature: _____________________________

Name: {{FIRM_PARTNER_NAME}}

Designation: Chartered Accountant

Date: _____________________________

---

*This engagement letter is confidential and intended solely for the authorized representative of {{CLIENT_NAME}}.*
"""

def save_letter_to_github(g, letter_content, client_name, variables):
    """Save approved letter to GitHub repository"""
    try:
        repo_name = st.secrets.get("github_repo", "")
        owner, repo = repo_name.split("/")
        repo_obj = g.get_user(owner).get_repo(repo)

        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"clients/{client_name.replace(' ', '_')}_EL_{timestamp}.md"

        # Add metadata header to letter
        metadata_header = f"""<!-- ENGAGEMENT LETTER METADATA
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Client: {client_name}
Service Type: {variables.get('SERVICE_TYPE', 'N/A')}
Fee: ₹{variables.get('FEE', 'N/A')}
Created By: {st.session_state.username}
Status: APPROVED
Repository: {repo_name}
-->

"""
        full_content = metadata_header + letter_content

        # Save to GitHub
        try:
            # Try to update if exists (shouldn't happen with timestamp)
            repo_obj.create_file(
                path=filename,
                message=f"Add engagement letter for {client_name}",
                content=full_content,
                branch="main"
            )

            # Also save metadata as JSON
            metadata = {
                "filename": filename,
                "client_name": client_name,
                "service_type": variables.get("SERVICE_TYPE", ""),
                "fee": variables.get("FEE", ""),
                "generated_date": datetime.now().isoformat(),
                "created_by": st.session_state.username,
                "status": "APPROVED",
                "repo_url": f"https://github.com/{repo_name}"
            }

            metadata_filename = f"clients/{client_name.replace(' ', '_')}_EL_{timestamp}_metadata.json"
            repo_obj.create_file(
                path=metadata_filename,
                message=f"Add metadata for {client_name} engagement letter",
                content=json.dumps(metadata, indent=2),
                branch="main"
            )

            return True, filename

        except Exception as e:
            st.error(f"❌ Error saving to GitHub: {str(e)}")
            return False, None

    except Exception as e:
        st.error(f"❌ GitHub error: {str(e)}")
        return False, None

def fetch_all_letters_from_github():
    """Fetch all approved letters from GitHub"""
    try:
        g = get_github_client()
        if not g:
            return []

        repo_name = st.secrets.get("github_repo", "")
        if not repo_name:
            return []

        owner, repo = repo_name.split("/")
        repo_obj = g.get_user(owner).get_repo(repo)

        letters = []
        try:
            # Get all files from clients folder
            contents = repo_obj.get_contents("clients")
            for item in contents:
                if item.name.endswith('_metadata.json'):
                    try:
                        metadata_content = item.decoded_content.decode('utf-8')
                        metadata = json.loads(metadata_content)
                        letters.append(metadata)
                    except:
                        pass
        except:
            pass

        return sorted(letters, key=lambda x: x.get('generated_date', ''), reverse=True)

    except Exception as e:
        st.warning(f"⚠️ Could not fetch letters: {str(e)}")
        return []

# ============================================================================
# SERVICE TYPE DEFAULTS
# ============================================================================

SERVICE_DEFAULTS = {
    "Full Statutory Audit": {
        "standards_1": "Standards on Auditing (SA) 315, 320, 330, 501, 505, 560",
        "standards_2": "Companies Act, 2013 & Auditor's Report & Order Rules, 2020",
        "deliverables": [
            "Audited Financial Statements (Balance Sheet, P&L, Cash Flow)",
            "Audit Report with Management Comments",
            "Management Letter with Observations & Recommendations"
        ],
        "timeline_months": 4
    },
    "Limited Review": {
        "standards_1": "Standard on Review Engagements (SRE) 2400",
        "standards_2": "Reviewed Statements Issued by ICAI",
        "deliverables": [
            "Reviewed Financial Statements",
            "Review Report",
            "Key Observations & Suggestions"
        ],
        "timeline_months": 2
    },
    "Income Tax Return": {
        "standards_1": "Income Tax Act, 1961 & CBDT Notifications",
        "standards_2": "Standards issued by ICAI for Tax Advisory",
        "deliverables": [
            "Income Tax Return (ITR-4 / ITR-5 / ITR-7)",
            "Tax Computation & Explanatory Notes",
            "Supporting Schedules & Reconciliations"
        ],
        "timeline_months": 3
    },
    "GST Advisory": {
        "standards_1": "Goods & Services Tax Act, 2017 & Rules",
        "standards_2": "CBIC Notifications, Circulars & Important Rulings",
        "deliverables": [
            "GST Return Filing (GSTR-1, GSTR-2, GSTR-3B)",
            "ITC Optimization & Compliance Report",
            "GST Regulatory Compliance Calendar"
        ],
        "timeline_months": 2
    },
    "Company Formation & Compliance": {
        "standards_1": "Companies Act, 2013 & Ministry of Corporate Affairs Rules",
        "standards_2": "Secretarial Standards issued by ICAI",
        "deliverables": [
            "Company Registration Assistance",
            "Compliance Calendar & Checklist",
            "Annual Compliance Reports & Filings"
        ],
        "timeline_months": 2
    }
}

# ============================================================================
# SESSION STATE
# ============================================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None

if "current_letter" not in st.session_state:
    st.session_state.current_letter = None
    st.session_state.current_variables = None

# ============================================================================
# LOGIN
# ============================================================================

def login_page():
    """Login screen"""
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown('<div class="header-main"><h1>📋 Engagement Letter Generator</h1><p>Cloud-Hosted Version</p></div>', unsafe_allow_html=True)

        username = st.text_input("Your Name", placeholder="e.g., Rajesh Kumar")
        password = st.text_input("Password", type="password", placeholder="Enter password")

        if st.button("Login", use_container_width=True, type="primary"):
            if password == "CA2026":
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success(f"✅ Welcome, {username}!")
                st.rerun()
            else:
                st.error("❌ Invalid password")

        st.markdown("---")
        st.info("""
        **Demo Password**: `CA2026`

        This is a cloud-hosted application for generating and managing engagement letters.
        Your work is automatically saved to a private GitHub repository.
        """)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_letter(template, variables):
    """Generate letter using Jinja2"""
    try:
        jinja_template = Template(template)
        return jinja_template.render(**variables)
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None

def generate_pdf(letter_content, client_name):
    """Generate PDF from letter content using fpdf2"""
    try:
        from fpdf import FPDF

        # Create PDF
        pdf = FPDF()
        pdf.add_page()

        # Set font
        pdf.set_font("Arial", size=10)

        # Add content line by line
        for line in letter_content.split('\n'):
            # Handle headings (lines with #)
            if line.startswith('## '):
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 8, line.replace('## ', ''), ln=True)
                pdf.set_font("Arial", size=10)
            elif line.startswith('### '):
                pdf.set_font("Arial", "B", 11)
                pdf.cell(0, 7, line.replace('### ', ''), ln=True)
                pdf.set_font("Arial", size=10)
            elif line.startswith('**') and line.endswith('**'):
                pdf.set_font("Arial", "B", 10)
                pdf.multi_cell(0, 5, line.replace('**', ''))
                pdf.set_font("Arial", size=10)
            elif line.strip() == '---':
                pdf.ln(2)
            elif line.strip() != '':
                pdf.multi_cell(0, 5, line.strip())
            else:
                pdf.ln(2)

        # Return PDF as bytes
        return pdf.output(dest='S').encode('latin-1')

    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")
        return None

# ============================================================================
# MAIN APP
# ============================================================================

def main_app():
    """Main application"""

    # Header
    st.markdown(f'<div class="header-main"><h2>📋 Engagement Letter Generator</h2><p>Logged in as: <strong>{st.session_state.username}</strong></p></div>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.markdown("**Cloud-Hosted Edition**")
        st.markdown("---")

        page = st.radio(
            "Navigation",
            ["📝 Generate Letter", "📚 All Letters", "⚙️ Settings", "❓ Help"],
            key="nav"
        )

        st.markdown("---")
        st.caption("🌐 Accessible from anywhere")
        st.caption("🔐 Private GitHub repository")
        st.caption("✅ Real-time sync")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.rerun()

    # ========================================================================
    # PAGE 1: GENERATE LETTER
    # ========================================================================

    if page == "📝 Generate Letter":
        st.markdown("# 📝 Generate Engagement Letter")
        st.markdown("Create a professional engagement letter and save to cloud.")
        st.markdown("---")

        service_type = st.selectbox(
            "Service Type *",
            list(SERVICE_DEFAULTS.keys())
        )

        defaults = SERVICE_DEFAULTS[service_type]

        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("### Client Information")
            client_name = st.text_input("Client Name *", placeholder="e.g., ABC Corp Ltd")
            client_pan = st.text_input("Client PAN (optional)", placeholder="e.g., ABCDE1234F")

        with col2:
            st.markdown("### Your Details")
            firm_name = st.text_input("Firm Name *", placeholder="e.g., XYZ & Associates")
            partner_name = st.text_input("Your Name (Partner) *", placeholder="e.g., Rajesh Kumar")

        st.markdown("---")
        st.markdown("### Service Details")

        service_description = st.text_area(
            "Service Description *",
            placeholder="Describe what you will do for the client...",
            height=80
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            timeline = st.selectbox(
                "Timeline *",
                ["1 month", "2 months", "3 months", "4 months", "5 months", "6 months"],
                index=2
            )

        with col2:
            fee = st.number_input("Fee (₹) *", min_value=5000, value=100000, step=5000)

        fee_terms = st.selectbox(
            "Payment Terms *",
            ["50% upfront, 50% on delivery", "100% upfront", "100% on delivery", "Monthly installments"]
        )

        st.markdown("---")

        if st.button("✨ Generate Engagement Letter", use_container_width=True, type="primary"):

            if not client_name or not firm_name or not partner_name or not service_description:
                st.error("❌ Please fill all required fields")
            else:
                timeline_months = int(timeline.split()[0])

                variables = {
                    "GENERATED_DATE": datetime.now().strftime("%d %B %Y"),
                    "CLIENT_NAME": client_name.upper(),
                    "CLIENT_PAN": client_pan if client_pan else "As per PAN records",
                    "FIRM_NAME": firm_name,
                    "FIRM_PARTNER_NAME": partner_name,
                    "CREATED_BY": st.session_state.username,
                    "ROLE": "Chartered Accountant",
                    "SERVICE_TYPE": service_type,
                    "SERVICE_DESCRIPTION": service_description,
                    "TIMELINE": timeline,
                    "INTERIM_WEEK": str(max(1, timeline_months // 2)),
                    "FINAL_WEEK": str(timeline_months * 4),
                    "FEE": f"{fee:,}",
                    "FEE_TERMS": fee_terms,
                    "DELIVERABLE_1": defaults["deliverables"][0],
                    "DELIVERABLE_2": defaults["deliverables"][1] if len(defaults["deliverables"]) > 1 else "As agreed",
                    "DELIVERABLE_3": defaults["deliverables"][2] if len(defaults["deliverables"]) > 2 else "Final delivery",
                    "STANDARDS_1": defaults["standards_1"],
                    "STANDARDS_2": defaults["standards_2"],
                }

                # Fetch template from GitHub
                template = fetch_master_template()

                # Generate letter
                letter = generate_letter(template, variables)

                if letter:
                    st.success("✅ Letter generated!")

                    st.markdown("### 📄 Preview")
                    st.markdown(letter)

                    st.session_state.current_letter = letter
                    st.session_state.current_variables = variables
                    st.session_state.current_client = client_name

                    st.markdown("---")
                    st.markdown("### 💾 Download & Save to Cloud")

                    col1, col2, col3 = st.columns([1, 1, 1])

                    with col1:
                        st.download_button(
                            label="📄 Download as Text",
                            data=letter,
                            file_name=f"{client_name.replace(' ', '_')}_EL.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    with col2:
                        pdf_data = generate_pdf(letter, client_name)
                        if pdf_data:
                            st.download_button(
                                label="📕 Download as PDF",
                                data=pdf_data,
                                file_name=f"{client_name.replace(' ', '_')}_EL.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )

                    with col3:
                        if st.button("☁️ Save to GitHub", use_container_width=True, type="primary"):
                            g = get_github_client()
                            if g:
                                success, filename = save_letter_to_github(g, letter, client_name, variables)
                                if success:
                                    st.success(f"✅ Saved to GitHub: {filename}")
                                    st.balloons()
                                else:
                                    st.error("❌ Failed to save")

    # ========================================================================
    # PAGE 2: ALL LETTERS
    # ========================================================================

    elif page == "📚 All Letters":
        st.markdown("# 📚 All Engagement Letters")
        st.markdown("View all approved letters from GitHub repository.")
        st.markdown("---")

        letters = fetch_all_letters_from_github()

        if letters:
            st.markdown(f"**Total Letters**: {len(letters)}")
            st.markdown("---")

            import pandas as pd
            df = pd.DataFrame(letters)

            # Display summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Letters", len(letters))
            with col2:
                st.metric("Total Fees", f"₹{sum([int(str(x).replace('₹', '').replace(',', '')) for x in df.get('fee', []) if x])}")
            with col3:
                st.metric("Created By", ", ".join(df['created_by'].unique()) if 'created_by' in df.columns else "Multiple")

            st.markdown("---")
            st.markdown("### Recent Letters")

            for letter in letters[:10]:  # Show last 10
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

                with col1:
                    st.markdown(f"**{letter.get('client_name', 'Unknown')}**")
                    st.caption(letter.get('service_type', 'N/A'))

                with col2:
                    st.caption(f"₹{letter.get('fee', 'N/A')}")

                with col3:
                    st.caption(letter.get('generated_date', 'N/A')[:10])

                with col4:
                    st.caption(f"By: {letter.get('created_by', 'Unknown')}")

                st.divider()

        else:
            st.info("📭 No letters yet. Generate your first letter!")

    # ========================================================================
    # PAGE 3: SETTINGS
    # ========================================================================

    elif page == "⚙️ Settings":
        st.markdown("# ⚙️ Settings")
        st.markdown("---")

        st.markdown("### GitHub Configuration")

        repo = st.secrets.get("github_repo", "Not configured")
        st.text_input("GitHub Repository", value=repo, disabled=True)

        st.markdown("### Cloud Deployment")
        st.info("""
        **This app is hosted on Streamlit Cloud**
        - Accessible from anywhere with internet
        - No installation required
        - Real-time GitHub sync
        - Secure authentication required
        """)

        st.markdown("### About")
        st.info("""
        **Engagement Letter Generator v3.0**
        - Cloud-hosted on Streamlit Cloud
        - Private GitHub repository for storage
        - Real-time collaboration enabled
        - ICAI-compliant audit trail
        """)

    # ========================================================================
    # PAGE 4: HELP
    # ========================================================================

    elif page == "❓ Help":
        st.markdown("# ❓ Help & Support")
        st.markdown("---")

        tab1, tab2, tab3 = st.tabs(["Getting Started", "Cloud Features", "FAQ"])

        with tab1:
            st.markdown("""
            ### How to Use

            1. **Generate Letter**
               - Select service type
               - Enter client & firm details
               - Click "Generate"

            2. **Review**
               - Check the preview
               - Edit in Word if needed

            3. **Save to GitHub**
               - Click "☁️ Save to GitHub"
               - Letter saved to cloud automatically
               - Accessible from anywhere

            4. **View All Letters**
               - Go to "📚 All Letters" tab
               - See all approved letters
               - Access anytime, anywhere
            """)

        with tab2:
            st.markdown("""
            ### Cloud Features

            ☁️ **Accessible Anywhere**
            - Share link with remote staff
            - No installation needed
            - Works on desktop, tablet, mobile

            🔐 **Secure GitHub Sync**
            - Private repository
            - Encrypted storage
            - Complete audit trail

            👥 **Team Collaboration**
            - Multiple users can generate letters
            - All letters in one GitHub repo
            - Real-time visibility

            📱 **Mobile Ready**
            - Works on any device
            - No app installation
            - Just open the link
            """)

        with tab3:
            st.markdown("""
            ### FAQ

            **Q: How do I share with remote staff?**
            A: Share the Streamlit Cloud link. They log in with password CA2026.

            **Q: Are my letters secure?**
            A: Yes. Private GitHub repo + password protection.

            **Q: Can multiple people use this?**
            A: Yes. Each person logs in with their name.

            **Q: Where are the letters stored?**
            A: Private GitHub repository (encrypted, secure).

            **Q: Can I access old letters?**
            A: Yes. Go to "📚 All Letters" to see entire history.

            **Q: What if GitHub is down?**
            A: You can still generate letters locally, save when GitHub is back.
            """)

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if st.session_state.authenticated:
        main_app()
    else:
        login_page()
