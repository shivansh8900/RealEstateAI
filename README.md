🏡 RealEstateAI — Intelligent Property Finder
🚀 Overview

RealEstateAI is a smart property chatbot that helps users find real estate projects based on their natural language queries.
You can ask questions like:

“Show me 3BHK flats in Pune under 80 lakhs.”
“Find under construction projects in Mumbai.”

The app filters property data (from CSV files) using AI-powered query understanding and displays the results using Streamlit.

🧠 Features

✅ Natural language property search
✅ Filter by BHK, City, Budget, Project Status, Locality, or Name
✅ Instant results with clean UI
✅ Fully deployed using Streamlit Cloud
✅ Persistent — stays online 24/7 (unlike ngrok)

🏗️ Project Structure
RealEstateAI/
│
├── app.py               # Streamlit frontend (user interface)
├── backend.py           # Chatbot logic and data filtering
├── ProjectAddress.csv   # Dataset - project address details
├── ProjectConfiguration.csv
├── ProjectConfigurationVariant.csv
├── project.csv
├── requirements.txt     # Required Python libraries
└── README.md            # You’re reading it!

⚙️ Tech Stack

Python 3.10+

Streamlit — for interactive web app

Pandas — for data manipulation

Regex (re) — for parsing user queries

💻 How to Run Locally

Clone this repository

git clone https://github.com/shivansh8900/RealEstateAI.git
cd RealEstateAI


Install dependencies

pip install -r requirements.txt


Run the Streamlit app

streamlit run app.py


🌐 Live Demo

Open the URL shown in the terminal https://realestateai-gxqjgkdx2tkzjr9e3salce.streamlit.app/ for live demo

🚀 Try it here: Live Streamlit App

📂 Data Files

The CSV files contain real estate data used by the chatbot:

ProjectAddress.csv → City, Locality, and Address details

ProjectConfiguration.csv → General configuration info

ProjectConfigurationVariant.csv → Variant-level details

project.csv → Main project names and metadata

🤖 Backend Logic

Extracts key filters (BHK, City, Budget, Status, Locality, Name) from user queries

Matches them against CSV data

Displays results dynamically in Streamlit UI

🧩 Example Queries

Try:
3BHK in Mumbai under 5 Cr

2BHK in Pune under 15 Cr


Properties in Mumbai

📜 Requirements
streamlit
pandas

✨ Credits

Developed by Shivansh Shrivastava

AI-powered property search built with ❤️ using Python & Streamlit.
