# Projects Portfolio

This repository contains a collection of data-driven mini projects focused on business analysis, forecasting, visualization, AI-assisted applications, and interactive Python tools.

## 1. Customer Data Analysis
This project analyzes customer order data to understand spending behavior, category trends, and customer segmentation.

- Dataset: customer orders data with product, category, customer, and revenue information
- Goal: identify high-value customers, top-selling products, and key revenue insights
- Files:
  - Customer Data Analysis/Customer_Orders_Analysis.ipynb
  - Customer Data Analysis/report.md
  - Customer Data Analysis/Datasets/customer_orders/customer_orders.csv

## 2. Forecasting
This project focuses on predicting temperature for upcoming weeks using historical weather data.

- Dataset: Delhi weather data
- Goal: build a forecast based on past patterns and trends
- Files:
  - Forecasting/weather_forcasting.ipynb
  - Forecasting/weather_data_delhi.csv

## 3. Visualization
This project visualizes COVID-19 case trends worldwide for selected countries using Python-based plotting libraries.

- Goal: explore and present global pandemic data in an interactive and readable form
- Files:
  - Visualization/Covid_Visualization.ipynb

## 4. Text-Based Adventure Game
This project is an interactive command-line adventure game in which the player explores an ancient land in search of legendary treasure.

- Objective: find the treasure by making strategic decisions and overcoming obstacles
- Gameplay: enter a player name, choose between a dark forest and a mysterious cave, and respond to location-specific challenges
- Functions:
  - `start_game()`: displays the introduction, collects the player's name, and starts the chosen path
  - `forest_path()`: handles the river and tree decisions
  - `cave_path()`: handles the torch and darkness decisions
  - `main()`: runs the game loop and offers the option to restart
- Outcomes:
  - Winning: follow the river or light the torch to find the treasure
  - Losing: climb the tree or proceed in the dark and end the quest
  - Restarting: replay the adventure after either outcome
- Files:
  - Adventure Game/adventure_game.py
  - Adventure Game/report.md
- Run command:
  - `python adventure_game.py`

## 5. Boston Housing Analysis
This project demonstrates a small, reproducible regression workflow for the Boston housing dataset: data loading, tabular analysis, optional EDA plots, and comparison of linear, Ridge, and Lasso regression.

- Dataset: Boston housing data from OpenML
- Goal: assess model performance and feature relationships in a classic regression task
- Files:
  - Boston-housing/boston_house_sklearn.py
  - Boston-housing/data.py
  - Boston-housing/analysis.py
  - Boston-housing/eda.py
  - Boston-housing/modeling.py
  - Boston-housing/README.md
- Run command:
  - `python boston_house_sklearn.py`

## 6. Nestlé HR Policy Assistant
This project is a local Gradio application for querying approved HR policy PDFs. It retrieves relevant passages, grounds answers in the source documents, and cites the associated PDF pages when responding.

- Features: policy indexing, semantic retrieval, prompt-grounded Q&A, source citations, and rebuildable local vector storage
- Tech stack: Python, PyPDF, Chroma, LangChain-style retrieval flow, and a Gradio UI
- Files:
  - Nestle HR Policy Assistant/app.py
  - Nestle HR Policy Assistant/README.md
  - Nestle HR Policy Assistant/.env.example
  - Nestle HR Policy Assistant/FINAL_REPORT.md
- Run command:
  - `python app.py`

## 7. NutriWise AI Calorie Tracker
NutriWise is a local-first calorie tracker that converts natural-language meal descriptions into nutrition estimates and maintains a daily meal log through a Gradio interface.

- Features: local food matching, daily calorie summaries, saved meal records, custom food management, and optional AI-powered estimation providers
- Estimation providers: local dataset, optional USDA FoodData Central, Gemini, OpenAI, and Ollama
- Goal: make nutrition tracking usable without requiring external credentials while supporting richer estimates when providers are configured
- Files:
  - Nutriwise_ai_llm_powered_calorie_tracker/app.py
  - Nutriwise_ai_llm_powered_calorie_tracker/nutrition.py
  - Nutriwise_ai_llm_powered_calorie_tracker/storage.py
  - Nutriwise_ai_llm_powered_calorie_tracker/data/healthy_meal_plans.csv
  - Nutriwise_ai_llm_powered_calorie_tracker/README.md
- Run command:
  - `python app.py`

## 8. AI-Powered LinkedIn Content Automation with n8n
This project automates LinkedIn content generation for a finance-focused brand using a FastAPI service, AutoGen-inspired agents, and n8n orchestration.

- Features: ideation, draft generation, heuristic quality scoring, hashtag suggestions, scheduling, approval flow, Slack review, and optional LinkedIn publishing
- Tech stack: Python, FastAPI, SQLite, n8n, Ollama/OpenAI-compatible models, and Slack/LinkedIn integrations
- Goal: create a repeatable thought-leadership content pipeline with human review and auditable delivery logs
- Files:
  - ai_powered_linkedin_content_automation_with_n8n/main.py
  - ai_powered_linkedin_content_automation_with_n8n/README.md
  - ai_powered_linkedin_content_automation_with_n8n/workflows/linkedin_content_automation.json
  - ai_powered_linkedin_content_automation_with_n8n/.env.example
- Run command:
  - `uvicorn main:app --reload --env-file .env`

## Summary
These projects demonstrate practical applications of Python, data analysis, forecasting, visualization, business intelligence, decision-support tools, workflow automation, and AI-assisted interactive applications.
