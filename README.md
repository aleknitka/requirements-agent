# Requirements Agent

A multi-skill agent for managing software and AI project requirements, meetings, and status reporting. Built on SQLite + sqlite-vec with Pydantic validation and optional OpenAI-compatible embedding for semantic search.

# Overview of functionaility

- Requirements agent is an expert in management of requirements for Data Science, ML and AI projects which cannot take advantage of a skilled professional. 
- Agent uses gitagent framework allowing it to be platform (Claude Code, Pi, Codex, etc) agnostic - agent can be converted to any major harnes using the command line tools.
- The agent can manage multiple projects, stored in `projects` directory, each project is refered to using the project `slug`.
    - Each project must consits of a `<SLUG>.db` and sqllite db with
    - `PROJECT.md` human readable summary of the project aims, stakeholders and progress. `PROJECT.md` must follow a certain template and be used by the agent to onboard itself each time we start up.
    - `logs` storage of daily logs, with no retention period (indefinate).
- Agent uses cli tools implemented in `src/requirements_agent_tools` to operate on databse. 
- Interaction with the agent happens via chat, in later stages an async analysis of transcripts, emails and documents will be implemented. 
- In later stages the agent will be given tools to join meetings and summarise multi-user chat conversation as well as transcripts. 
- Agent asks claryfing questions to obtain information about the project from the user. 
- Key askepct of the interview is to get as much information as possible from the user to eliminate all assumption and clarify requirements for the application. 
- once the interview is concluded agent will refine the requirement and once user approves the requirement is saved to the databse.
- all operations on database are logged into daily log, as well as into the updates table of the db, alongside the diff of changes.
- IN LATER Stage we will implement mechanisms of formalisation such as FRET, however this is out of scope for this phase.
- AIMS for PHASE 1:
1. implement db cli and enable it's use be the agent, in particular:
    a. agent should be able to detect if there are any valid projects in the projects folder, and create a new one if there aren't any, if a single project exists then inform user that we are talking about the project, and allow user to select roject if there are multiple ones present. 
    b. user should be able to initiate a new project via conversation
    c. each new project must result in required files and intervew by the agent
    d. agent must be able to create, update and search the requirements in the db
    e. all operations agent takes with cli MUST be logged to daily log file and updates loged into the updates table in the db
    f. agent must be able to read from the updates table based on multiple criteria (data, type, id, etc)
    g. agent is able to get a human-readable full stock of requiremens from the db, each with all fields printed and updates made. This should be handled with jinja or other template and return a pdf - for audit purposes. 
    x. see code in the src as most of the functionality in cli has been updated - however ensure that all code is maintainable and easy to follow as well as documented well with google docstrings

- AIMS for PHASE 2:
    a. implement ability for an agent to review open/new requirements and record issues for that can be addressed with stakeholders - add ISSUES table (create a good schema first), this will be used as a todo list and periodically reviewed by the agent for answers.
    b. formalisation - we will create a skills and methods for few formalisation methods - user will be able to select a method and agent will formalise teh requirements, save them in the database

- AIMS for PHASE 3:
    a. agent is able to ingest unstructured information from text files (md, txt, pdf, etc) as well as email. It can use this information to update requirements, logs and issues. Evidecne is linked and recorded in teh DB. 
    b. agent has an ability to work in autonomous way - some kind of wake up daily and standard task performance (ideation, reasearch)
    c. implementation of the async autonomous work (see b)

- AIMS for PHASE 4:
    a. agent is able to join chats on Slack, MS Teams, Telegram and summarise conversations and assign decisions - MEETINGS table is created and stores updates from the meetings for full audit trial. 