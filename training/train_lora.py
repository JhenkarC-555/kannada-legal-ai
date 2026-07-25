# training/train_lora.py

import os
import yaml
from pathlib import Path
from loguru import logger

CONFIG_PATH = Path("training/configs/lora_config.yaml")

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)

def train():
    cfg = load_config()
    logger.info(f"Starting QLoRA fine-tuning for model: {cfg['model']['name']}")
    
    try:
        import torch
        from transformers import (
            AutoModelForCausalLM, AutoTokenizer,
            TrainingArguments, BitsAndBytesConfig,
        )
        from peft import (
            LoraConfig, get_peft_model,
            prepare_model_for_kbit_training, TaskType,
        )
        from trl import SFTTrainer
        from training.dataset_loader import load_split
    except ImportError as e:
        logger.error(f"Missing required ML libraries: {e}")
        logger.info("Run on Colab: pip install transformers peft bitsandbytes trl datasets")
        return

    # 1. 4-bit Quantization Config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=cfg["quantization"]["load_in_4bit"],
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type=cfg["quantization"]["bnb_4bit_quant_type"],
        bnb_4bit_use_double_quant=cfg["quantization"]["bnb_4bit_use_double_quant"],
    )

    # 2. Tokenizer & Base Model
    tokenizer = AutoTokenizer.from_pretrained(
        cfg["model"]["name"], trust_remote_code=True
    )
    tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        cfg["model"]["name"],
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)

    # 3. LoRA Configuration
    lc = cfg["lora"]
    peft_config = LoraConfig(
        r=lc["r"],
        lora_alpha=lc["lora_alpha"],
        lora_dropout=lc["lora_dropout"],
        target_modules=lc["target_modules"],
        bias=lc["bias"],
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, peft_config)
    model.print_trainable_parameters()

    # 4. Training Arguments
    t = cfg["training"]
    training_args = TrainingArguments(
        output_dir=t["output_dir"],
        num_train_epochs=t["num_train_epochs"],
        per_device_train_batch_size=t["per_device_train_batch_size"],
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"],
        fp16=t["fp16"],
        logging_steps=t["logging_steps"],
        save_steps=t["save_steps"],
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        report_to=t.get("report_to", "none"),
        warmup_ratio=t.get("warmup_ratio", 0.03),
        lr_scheduler_type=t.get("lr_scheduler_type", "cosine"),
    )

    # 5. SFT Trainer Setup
    trainer = SFTTrainer(
        model=model,
        args=training_args,
        train_dataset=load_split("train"),
        eval_dataset=load_split("val"),
        tokenizer=tokenizer,
        dataset_text_field="text",
        max_seq_length=t["max_seq_length"],
    )

    logger.info("Training started...")
    trainer.train()

    save_path = os.path.join(t["output_dir"], "best_model")
    trainer.save_model(save_path)
    tokenizer.save_pretrained(save_path)
    logger.success(f"Training complete! Best model saved to: {save_path}")

if __name__ == "__main__":
    train()