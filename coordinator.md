Right now the tools I have are the following:
1. A module that can browser through websites to collecte required information, fill forms and navigate. We have strict conditions to abide ReCAPTCHA rules and not go beyond if it hits a Captcha wall
2. A module that can do, with given instructions and phone number, can call a business and make reservations or provide clarifications for the users
3. A module that is capable of searching anything on the web, including websites, maps and everything inclusive of it.
4. A module that can use Handelsregister.ai to get official business information (including website URL and phone numbers)
5. A module that can access e-mails, calendars (write, read) from users' Google Accounts.

I need to create a coordinator model that can perform the following:
1. Derive main steps to perform without any user-intervention. This means, to evaluate that the original prompt that the coordinator model receives has all the information to perform it without any additional information. Reject the prompt request if this is not passed. The coordinator has access to all the agents irrespective of the process to derive required information and to process the prompt. The steps should be in a process map, such that either multiple steps can be spawned in parallel if there are no dependencies between processes, or wait until a dependency finishes the job, process the return output and then pass to the next step. The coordinator is responsible to "spawn" these agents/steps as and when required. I'd imagine the steps schema to look like this:
{
	step_id: uuid,
	step_name: Get Contact Info from Handelsregister,
	tool_module_involved: true,
	tool_module_name: handelsregister,
	dependencies: [], //if this is not empty, the step_id will be in the dependencies
	prompt_message: "The company name is LAP Coffee, I'd need the phone number, email, physical address and the Website URL"
}

The steps should be as detailed as possible, with the prompt message as crisp and precise as possible. The composition of steps about primary, secondary, tertiary fallbacks, with one definitely working fallback. Usually the final fallback is that the email/calendar module is called to create a calendar appointment in a free slot with the next steps that the user should perform. For example, in a hotel reservation, if an online reservation failed, and the phone call failed, and the web searches didn't return anything, the coordinator prepares a step process of what the user should search for, who to call, and what to ask - and puts this in the calendar appointment notes, and sets the appointment in a time that's actionable enough for the user, but in a free slot where he/she can see it. Each step of the increasing fallback degrades on the automation possible, and increases user intervention/action.

2. The coordinator should create these steps and store it in a DB, maybe Directus/Firebase. I haven't decided on schema yet, but it's mostly process_id against the list of steps, and information of the current step(s).
3. Once the process flow is complete, the coordinator should consolidate all the responses/outputs, preferences from the user in the prompt, and create a knowledge base in another table in the same DB. I don't know how to create this knowledge base that can scale properly and can be retrieved faster. For example, my motive is that: for the first time, the user might say hey, find out if they have hamburgers in Mc'Donalds -the coordinator performs the whole workflow and successfully knows this information now. I need Mc'Donalds to be saved in the list of restaurants that the user has spoken about, and for the fact if they have hamburgers in Mc'Donalds. I don't know how to create this schema but this is something I'd need, so when the user just asks "Do we have hamburgers now", the coordinator immediately maps the hamburgers in Mc'Donalds, even if the user didn't mention the place name.