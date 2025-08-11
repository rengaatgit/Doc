my company expose endpoints to access llm models with spec: 1. generic endpoint (www.ep.net/v1/chat/completion) 2. model is part of payload , not part of param to llm I am using llamaindex version > 0.10.0 , how I can do api call using llamaindex 
give me py coding in one file.



you are trade domain expert with expertise in Documentary Trade finance especially with Letter of credit, UCP600 and ISBP745.
You are Gen-AI, RAG and python coding expert as well.
the sample letter of credit(LC) files and mappings.csv are attached for your reference.

We are using gpt-4o as our LLM and As per first column of mapping.csv, let llm extract the value from LC file and create a dictionary with first column of mapping.csv as key and extracted value as value of the dictionary 

You need to create 30 tasks for validation check according to entries in mapping.csv. each entry should have the 6 following items as it's elements

element1: key of the above dictionary 
element2: value of the above dictionary
element3: 2nd column of mapping.csv
element4: 3rd column of mapping.csv (dummy data is used for this sample coding, later actual data will be fed)
element5: 4th column of mapping.csv
element6: 5th column of mapping.csv (dummy data is used for this sample coding, later actual data will be fed)

We are using gpt-4o as our LLM and Validation should be done by this LLM in such a way that whether 2nd element (extracted value from LC) is compliant with both 4th Element (Articles text)and 6th element (Paragraphs text), so 1st, 2nd, 4th, and 6th elements should be sent to gpt-4o along with detailed and well-explained prompt to do compliance check. 

you need to create a agent using langgraph to pickup one task from above 32 tasks at a time and it should use LLM(gpt-4o) for the task execution. once current validation task is completed, then Agent has to update current task result in tabular format with 6 columns:
column1: 1st element from task
column2: 2nd element from task
column3: 3rd element from task
column4: 5th element from task
compliant status as 5th column
remarks as 6th column. 
And then agent has to pick up next task and update the above result table. repeat this process till completion of 30 tasks.

Simply put the whole story in one line: let llm(gpt-4o) extract data from LC & create temp. dictionary and then langgraph-agent powered by LLM(gpt-4o) has to do compliance check against column3 & colunm5 of csv files for all 30 items in mapping.csv  

provide me final workable python coding in one file.
