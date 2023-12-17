from glancenote.models import Assistant
from openai import OpenAI

client = OpenAI()

def get_or_create_assistant(user):
    try:
        user_assistant = Assistant.objects.get(user=user)
        assistant_id = user_assistant.assistant_id
        assistant = client.beta.assistants.retrieve(assistant_id)
    except Assistant.DoesNotExist:
        assistant = create_new_assistant()
        Assistant.objects.create(user=user, assistant_id=assistant.id)
    except Exception as e:
        # Handle other exceptions such as API errors
        print(f"Error: {e}")
        assistant = None

    return assistant


def create_new_assistant():
    # Define assistant parameters
    assistant_name = "Teacher Assistant"
    description="You are a teacher assistant. Your job is to read files and answer questions based on the content of the files. You are great at reading specific data and outputting data based on what you read. You analyze data present in .csv files, understand trends, and come up with the corresponding data to the prompt."
    model = "gpt-4-1106-preview"
    tools = [{"type": "code_interpreter"}, {"type": "retrieval"}]
    file_ids = []

    try:
        assistant = client.beta.assistants.create(
            name=assistant_name,
            description=description,
            model=model,
            tools=tools,
            file_ids=file_ids
        )
        return assistant
    except Exception as e:
        print(f"Error creating assistant: {e}")
        return None

def get_saved_assistant_id():
    # Implement logic to retrieve the saved assistant ID
    # This could be from a database, a file, or an environment variable
    pass

def save_assistant_id(assistant_id):
    # Implement logic to save the assistant ID
    # This could be in a database, a file, or an environment variable
    pass
