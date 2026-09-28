import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
import streamlit as st

from dotenv import load_dotenv

from backend.document_utils.formatters import (
    text_to_docx,
    text_to_pdf,
    text_to_txt
)


load_dotenv()


API_URL = os.getenv(
    "LEGALEASE_API_URL",
    "http://127.0.0.1:8000"
)


# ==================================
# PAGE CONFIG
# ==================================

st.set_page_config(

    page_title="LegalEase",

    page_icon="⚖️",

    layout="wide"
)


# ==================================
# CUSTOM CSS
# ==================================

st.markdown(
    """
    <style>

    .main-title {

        font-size: 42px;

        font-weight: 800;

        margin-bottom: 0;

    }


    .subtitle {

        color: #666;

        font-size: 17px;

    }


    .legal-notice {

        padding: 12px 16px;

        border-radius: 10px;

        border: 1px solid #ddd;

        background: #fafafa;

    }

    </style>
    """,

    unsafe_allow_html=True
)


# ==================================
# HEADER
# ==================================

logo_path = os.path.join(

    os.path.dirname(
        os.path.dirname(__file__)
    ),

    "assets",

    "logo.png"
)


col1, col2 = st.columns(
    [1, 7]
)


with col1:

    if os.path.exists(
        logo_path
    ):

        st.image(
            logo_path,
            width=85
        )


with col2:

    st.markdown(
        '<p class="main-title">'
        'LegalEase'
        '</p>',

        unsafe_allow_html=True
    )


    st.markdown(
        '<p class="subtitle">'
        'AI-powered legal document generation platform'
        '</p>',

        unsafe_allow_html=True
    )


# ==================================
# LEGAL NOTICE
# ==================================

st.markdown(

    '<div class="legal-notice">'
    '⚠️ <b>Legal notice:</b> '
    'LegalEase creates AI-assisted drafts. '
    'Review the generated document with a '
    'qualified legal professional before '
    'signing or relying on it.'
    '</div>',

    unsafe_allow_html=True
)


# ==================================
# SESSION STATE
# ==================================

if "document" not in st.session_state:

    st.session_state.document = ""


# ==================================
# SIDEBAR
# ==================================

with st.sidebar:

    st.header(
        "Document Type"
    )


    document_type = st.selectbox(

        "Choose a document",

        [

            "Employment Contract",

            "Non-Disclosure Agreement (NDA)",

            "Lease Agreement",

            "Service Agreement",

            "Custom Legal Document"

        ]

    )


    jurisdiction = st.text_input(

        "Jurisdiction / Governing Law",

        placeholder="Example: Tamil Nadu, India"

    )


    st.divider()


    st.caption(
        "LegalEase • "
        "FastAPI → Gemini → Document"
    )


# ==================================
# INPUT
# ==================================

st.header(
    "1. Enter Document Details"
)


left, right = st.columns(
    2
)


with left:

    parties = st.text_area(

        "Parties / Involved Persons",

        height=170,

        placeholder=
        """
Party A: ABC Technologies Pvt. Ltd.

Party B: John Doe

Addresses / roles if applicable...
        """

    )


    effective_date = st.text_input(

        "Effective Date",

        placeholder=
        "Example: 1 October 2026"

    )


with right:

    terms = st.text_area(

        "Terms & Conditions",

        height=170,

        placeholder=
        """
Salary / rent / payment terms

Duration

Responsibilities

Confidentiality

Termination / notice period...
        """

    )


    additional_details = st.text_area(

        "Additional Details",

        height=100,

        placeholder=
        "Any other information or clauses..."

    )


# ==================================
# GENERATE BUTTON
# ==================================

st.header(
    "2. Generate"
)


if st.button(

    "✨ Generate Legal Document",

    type="primary",

    use_container_width=True

):

    if not parties.strip():

        st.error(
            "Please enter the parties."
        )


    elif not terms.strip():

        st.error(
            "Please enter the terms."
        )


    elif not effective_date.strip():

        st.error(
            "Please enter the effective date."
        )


    else:

        payload = {

            "document_type":
                document_type,

            "parties":
                parties,

            "terms":
                terms,

            "effective_date":
                effective_date,

            "jurisdiction":
                jurisdiction
                or "Not specified",

            "additional_details":
                additional_details
        }


        with st.spinner(

            "Gemini is generating "
            "the document..."

        ):

            try:

                response = requests.post(

                    f"{API_URL}/api/generate",

                    json=payload,

                    timeout=120
                )


                if response.ok:

                    st.session_state.document = (

                        response
                        .json()
                        ["document"]
                    )


                    st.success(

                        "Document generated successfully."
                    )


                else:

                    try:

                        detail = (

                            response
                            .json()
                            .get(
                                "detail",
                                response.text
                            )
                        )

                    except Exception:

                        detail = response.text


                    st.error(
                        f"Backend error: {detail}"
                    )


            except requests.RequestException as error:

                st.error(

                    "FastAPI backend is not reachable.\n\n"
                    f"{error}"

                )


# ==================================
# EDITABLE PREVIEW
# ==================================

st.header(
    "3. Editable Preview"
)


edited_document = st.text_area(

    "Edit your document here",

    value=st.session_state.document,

    height=600

)


st.session_state.document = (
    edited_document
)


# ==================================
# DOWNLOAD
# ==================================

if st.session_state.document.strip():

    st.header(
        "4. Download"
    )


    d1, d2, d3 = st.columns(
        3
    )


    # TXT
    with d1:

        st.download_button(

            "📄 Download TXT",

            data=text_to_txt(
                st.session_state.document
            ),

            file_name=
                "legalease_document.txt",

            mime=
                "text/plain",

            use_container_width=True

        )


    # DOCX
    with d2:

        st.download_button(

            "📝 Download DOCX",

            data=text_to_docx(
                st.session_state.document
            ),

            file_name=
                "legalease_document.docx",

            mime=
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",

            use_container_width=True

        )


    # PDF
    with d3:

        try:

            pdf_data = text_to_pdf(

                st.session_state.document

            )


            st.download_button(

                "📑 Download PDF",

                data=pdf_data,

                file_name=
                    "legalease_document.pdf",

                mime=
                    "application/pdf",

                use_container_width=True

            )


        except Exception as error:

            st.error(
                f"PDF generation failed: {error}"
            )


# ==================================
# FOOTER
# ==================================

st.divider()


st.caption(
    "LegalEase — "
    "AI-assisted document automation"
)