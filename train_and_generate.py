import os
from transformers import TextDataset, DataCollatorForLanguageModeling
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from transformers import Trainer, TrainingArguments

def load_dataset(file_path, tokenizer, block_size=128):
    dataset = TextDataset(
        tokenizer=tokenizer,
        file_path=file_path,
        block_size=block_size,
    )
    return dataset

def load_data_collator(tokenizer):
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer, 
        mlm=False,
    )
    return data_collator

def train(train_file_path, model_name,
          output_dir,
          overwrite_output_dir,
          per_device_train_batch_size,
          num_train_epochs,
          save_steps):
          
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    train_dataset = load_dataset(train_file_path, tokenizer)
    data_collator = load_data_collator(tokenizer)

    tokenizer.save_pretrained(output_dir)
    
    model = GPT2LMHeadModel.from_pretrained(model_name)

    training_args = TrainingArguments(
        output_dir=output_dir,
        overwrite_output_dir=overwrite_output_dir,
        per_device_train_batch_size=per_device_train_batch_size,
        num_train_epochs=num_train_epochs,
        save_steps=save_steps,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        data_collator=data_collator,
        train_dataset=train_dataset,
    )
        
    trainer.train()
    trainer.save_model()

def generate_text(model_path, prompt_text):
    tokenizer = GPT2Tokenizer.from_pretrained(model_path)
    model = GPT2LMHeadModel.from_pretrained(model_path)
    
    encoded_input = tokenizer(prompt_text, return_tensors='pt')
    output = model.generate(
        **encoded_input, 
        max_length=200, 
        num_return_sequences=1,
        temperature=0.9,
        top_k=50,
        top_p=0.95,
        do_sample=True
    )
    
    print(tokenizer.decode(output[0], skip_special_tokens=True))

if __name__ == "__main__":
    # Check if lyrics file exists
    if not os.path.exists("yeat_lyrics.txt"):
        print("Please run scrape_lyrics.py first to generate yeat_lyrics.txt")
    else:
        # Train
        print("Starting training... (this may take a while)")
        train(
            train_file_path='yeat_lyrics.txt',
            model_name='gpt2', # using base gpt2
            output_dir='yeat_model',
            overwrite_output_dir=True,
            per_device_train_batch_size=4,
            num_train_epochs=3,
            save_steps=500
        )
        
        # Generate
        print("\n\nGenerated Song:\n")
        generate_text('yeat_model', "twizzy")
