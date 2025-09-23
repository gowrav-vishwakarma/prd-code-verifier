This is a PRD corss verifier project made in python to verify users code along its documentaiotns.

What we want is

1: User must create, save and open projects that will be simply json files containing following

- Load project button: user will select pre saved project file and fill the below form.
- Project name
- Output folder select
- Global System Prompt Text Area
- Global Instructions Text Area
- Faility to add rows of various verification sections containing
  - name of verification
  - documentation files (multiple) selection
  - frontend code files (multiple) selection
  - backend code files (muiltiple) selection
  - checkbox : to override global system prompt
  - checkbox: to override global instructions
  - varification system prompt text area
  - varification instruction text area
- Svae button to generate all in json and allo wuser to save on their storage.

2: We can run all verifications in one go or can run each verification by its own also.

3: System must read env file for mode of AI selection

- User want to use Ollama, LM Studio, Geminiy or openAI compatible API
- required keys for selected mode of AI engagement

4: How the system will run verification

- When run (all) system do the follwoing for all verifications set in rows above
- when run for specific system will do the same for specific verification as follows

5: How the system should work

- system will generate a long prompt containing

  - Global System Prompt or Each Verification's local System prompt if overrided by rows checkbox
  - Then the system will add documetations content appended in the prompt in proper format with file name (with path) and its content below
  - Then system will provide Frontend code to prompt with file name (with path) appending prompt
  - Then system will append backend files (with path) and code in prompt
  - Global Instructions will be appende din last or local verification instruiction if overrided in row.

- Then system will engage the AI LLM giving the prompt and will kake response and will save the response in given output folder with file name name of verification + "\_report" in md format.
