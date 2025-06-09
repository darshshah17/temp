import subprocess
import re

# File path for output
output_file = "generated_sentences.txt"

# Open the file in append mode initially to clear previous data
open(output_file, "w").close()

def run_ollama(prompt, target_sentence_count=10000):
    model_name = "llama3.2"
    sentences = []
    
    try:
        while len(sentences) < target_sentence_count:
            result = subprocess.run(
                ["ollama", "run", model_name],
                input=prompt,
                capture_output=True,
                text=True,
                check=True
            )

            temp = result.stdout.strip()
            if not temp:
                print("No output generated; re-running...")
                continue  # Retry if no output was generated

            # Split the output while keeping punctuation
            temp_sentences = re.split(r"(?<=[.!?])\s+", temp)
            
            new_sentences = []
            for sentence in temp_sentences:
                # Only add sentences that are non-empty and if we haven’t reached the target
                if len(sentence.strip()) and len(sentences) < target_sentence_count:
                    new_sentences.append(sentence.strip())
            
            # Extend the main list and write new sentences to the file
            sentences.extend(new_sentences)

            # Write the new batch of sentences to the file
            with open(output_file, "a") as file:
                file.write("\n".join(new_sentences) + "\n")
            
            print(f"Current count: {len(sentences)} sentences")

    except subprocess.CalledProcessError as e:
        print("Error running Ollama:", e.stderr)

# Prompt for generating diverse sentences
prompt = "Give me around 20 random medium-length sentences that a person would say or write in their diary that express various different feelings (both positive and negative) and are separated by periods. Use different sentence structures and vary the wording. In your response, only include the twenty sentences, separated by periods, i dont want ANY OTHER TEXT that is not asked for (no numbering, no response saying (Here are 20 random sentences for your request:)"

# Run the script
run_ollama(prompt)
