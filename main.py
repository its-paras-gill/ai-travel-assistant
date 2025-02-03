from travel_assistant import TravelAssistant
 
if __name__ == "__main__":
    assistant = TravelAssistant()
    user_input = input("Enter your travel plan: ")
    assistant.process_travel_plan(user_input)
    
    while True:
        user_query = input("\nAsk a travel-related question (or type 'exit' to quit): ")
        if user_query.lower() == "exit":
            break

        response = assistant.process_query(user_query)
        print(f"Assistant: {response}")