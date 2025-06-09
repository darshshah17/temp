import subprocess

# Input and output file paths
input_file = "generated_sentences.txt"
output_file = "trainingData.txt"

def analyze_sentence(sentence):
    model_name = "llama3.2"
    prompt = f"""sentence: {sentence}, based on this phrase, determine the following traits of the music the user 
    would likely prefer to listen to at the present moment:
    danceability (0.00-1.00 describing rhythmic quality and suitability for music with an upbeat feel), 
    and energy (0.00-1.00 representing a measure of intensity and activity).
    Interpret danceability as if upbeat or rhythmically engaging music matches the user's mood, e.g a person in a bad mood likely wouldn't want dancey music.
    The output should be ONLY a comma-separated value of danceability, energy, with a minimum of 2 decimal places. NOTHING ELSE, no words or justification is needed from you.
    """
    
    try:
        # Run Ollama with the prompt
        result = subprocess.run(
            ["ollama", "run", model_name],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Capture and return the output
        return result.stdout.strip()
    
    except subprocess.CalledProcessError as e:
        print("Error running Ollama:", e.stderr)
        return None

with open(input_file, "r") as infile, open(output_file, "w") as outfile:
    batch = []
    for i, line in enumerate(infile):
        try:
            sentence = line.strip()
            if sentence:
                # Get the danceability and energy scores from analyze_sentence
                temp = analyze_sentence(sentence)
                if temp:
                    temp = [max(float(i), 0) for i in temp.split(",")]
                    analysis = [sentence] + temp  # Append sentence and scores together

                    # Convert list to comma-separated string and write to file
                    outfile.write(",".join(map(str, analysis)) + "\n")
                    batch.append(analysis)  # Add to batch for reference
                    print(i)
                else:
                    print(f"Failed to analyze line {i}")
        except Exception as e:
            print(f"Error processing line {i}: {e}")
            continue
                    
print("Batch analysis completed:", batch)
