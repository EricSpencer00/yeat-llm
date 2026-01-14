import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import os

# Colors for terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

class YeatBot:
    def __init__(self, model_path='yeat_model'):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please run train_model.py first.")
        
        print(f"Loading YeatBot from {model_path}...")
        self.tokenizer = GPT2Tokenizer.from_pretrained(model_path)
        # Ensure pad token is set to avoid warnings
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        self.model = GPT2LMHeadModel.from_pretrained(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.model.to(self.device)

    def generate_song(self, prompt="twizzy", max_length=300, temperature=0.8):
        """Generates a full song based on a prompt."""
        print(f"\n--- Generating Yeat Song (Prompt: {prompt}) ---")
        
        encoded_input = self.tokenizer(prompt, return_tensors='pt').to(self.device)
        
        output = self.model.generate(
            **encoded_input,
            max_length=max_length,
            num_return_sequences=1,
            temperature=temperature,
            top_k=50,
            top_p=0.95,
            do_sample=True,
            repetition_penalty=1.2,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        song = self.tokenizer.decode(output[0], skip_special_tokens=True)
        return song

    def chat(self):
        """Interactive chat mode with the Yeat model."""
        print(f"\n{MAGENTA}TwizzyBot is active.{RESET} Type 'quit' to exit.")
        print(f"{CYAN}Tip:{RESET} Use Yeat-style prompts like 'I just pulled up' or 'Luh geek'.\n")
        
        while True:
            user_input = input(f"{GREEN}You:{RESET} ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            # Use __call__ instead of encode to get attention_mask
            inputs = self.tokenizer(user_input, return_tensors='pt').to(self.device)
            
            output = self.model.generate(
                **inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.9,
                top_k=50,
                top_p=0.95,
                do_sample=True,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=2
            )
            
            response = self.tokenizer.decode(output[0], skip_special_tokens=True)
            # Remove the user input from the response to make it look like a reply
            reply = response[len(user_input):].strip()
            # If reply is empty, just show the whole thing
            if not reply:
                reply = response
                
            print(f"{MAGENTA}Yeat:{RESET} {reply}\n")

if __name__ == "__main__":
    bot = YeatBot()
    
    # 1. Generate a sample song
    print(bot.generate_song(prompt="Luh geek"))
    
    # 2. Enter chat mode
    bot.chat()
