import gradio as gr

from extensions.sd_dreambooth_extension.dreambooth import conversion, dreambooth
from extensions.sd_dreambooth_extension.dreambooth.db_config import DreamboothConfig
from extensions.sd_dreambooth_extension.dreambooth.dreambooth import get_db_models, performance_wizard, \
    training_wizard, training_wizard_person, log_memory, generate_sample_img
from modules import script_callbacks, sd_models, shared
from modules.ui import setup_progressbar, gr_show, wrap_gradio_call
from webui import wrap_gradio_gpu_call


def on_ui_tabs():
    with gr.Blocks() as dreambooth_interface:
        db_save_params = gr.Button(value="Save Params", elem_id="db_save_config")
        with gr.Row(equal_height=True):
            db_model_dir = gr.Dropdown(label='Model', choices=sorted(get_db_models()))
            db_half_model = gr.Checkbox(label="Half", value=False)
            db_load_params = gr.Button(value='Load Params')
            db_generate_checkpoint = gr.Button(value="Generate Ckpt")
            db_interrupt_training = gr.Button(value="Cancel")
            db_train_embedding = gr.Button(value="Train", variant='primary')

        with gr.Row().style(equal_height=False):
            with gr.Column(variant="panel"):
                with gr.Tab("Create Model"):
                    db_new_model_name = gr.Textbox(label="Name")
                    db_create_from_hub = gr.Checkbox(label="Import Model from Huggingface Hub", value=False)
                    with gr.Column(visible=False) as hub_row:
                        db_new_model_url = gr.Textbox(label="Model Path", value="runwayml/stable-diffusion-v1-5")
                        db_new_model_token = gr.Textbox(label="HuggingFace Token", value="")
                    with gr.Row() as local_row:
                        src_checkpoint = gr.Dropdown(label='Source Checkpoint',
                                                     choices=sorted(sd_models.checkpoints_list.keys()))
                    diff_type = gr.Dropdown(label='Scheduler', choices=["ddim", "pndm", "lms"], value="ddim")

                    with gr.Row():
                        with gr.Column(scale=3):
                            gr.HTML(value="")

                        with gr.Column():
                            db_create_embedding = gr.Button(value="Create", variant='primary')
                with gr.Tab("Parameters"):
                    with gr.Accordion(open=True, label="Settings"):
                        db_train_wizard_person = gr.Button(value="Training Wizard (Person)")
                        db_train_wizard_object = gr.Button(value="Training Wizard (Object/Style)")
                        with gr.Column():
                            gr.HTML(value="Intervals")
                            db_max_train_steps = gr.Number(label='Training Steps', value=1000, precision=0)
                            db_num_train_epochs = gr.Number(label="Training Epochs", precision=0, value=1)
                            db_save_embedding_every = gr.Number(
                                label='Save Checkpoint Frequency', value=500,
                                precision=0)
                            db_save_preview_every = gr.Number(
                                label='Save Preview(s) Frequency', value=500,
                                precision=0)

                        with gr.Column():
                            gr.HTML(value="Learning Rate")
                            db_learning_rate = gr.Number(label='Learning Rate', value=1.72e-6)
                            db_scale_lr = gr.Checkbox(label="Scale Learning Rate", value=False)
                            db_lr_scheduler = gr.Dropdown(label="Learning Rate Scheduler", value="constant",
                                                          choices=["linear", "cosine", "cosine_with_restarts",
                                                                   "polynomial", "constant",
                                                                   "constant_with_warmup"])
                            db_lr_warmup_steps = gr.Number(label="Learning Rate Warmup Steps", precision=0, value=0)

                        with gr.Column():
                            gr.HTML(value="Instance Image Processing")
                            db_resolution = gr.Number(label="Resolution", precision=0, value=512)
                            db_center_crop = gr.Checkbox(label="Center Crop", value=False)
                            db_hflip = gr.Checkbox(label="Apply Horizontal Flip", value=True)
                        db_pretrained_vae_name_or_path = gr.Textbox(label='Pretrained VAE Name or Path',
                                                                    placeholder="Leave blank to use base model VAE.",
                                                                    value="")

                        db_use_concepts = gr.Checkbox(label="Use Concepts List", value=False)
                        with gr.Column():
                            gr.HTML(value="Concepts")
                            db_concepts_path = gr.Textbox(label="Concepts List",
                                                          placeholder="Path to JSON file with concepts to train.")

                    with gr.Accordion(open=False, label="Advanced"):
                        with gr.Row():
                            with gr.Column():
                                db_performance_wizard = gr.Button(value="Auto-Adjust (WIP)")
                                with gr.Column():
                                    gr.HTML(value="Batch")
                                    db_train_batch_size = gr.Number(label="Batch Size", precision=0, value=1)
                                    db_sample_batch_size = gr.Number(label="Class Batch Size", precision=0, value=1)
                                with gr.Column():
                                    gr.HTML(value="Tuning")
                                    db_use_cpu = gr.Checkbox(label="Use CPU Only (SLOW)", value=False)
                                    db_use_8bit_adam = gr.Checkbox(label="Use 8bit Adam", value=False)
                                    db_mixed_precision = gr.Dropdown(label="Mixed Precision", value="no",
                                                                     choices=["no", "fp16", "bf16"])
                                    db_attention = gr.Dropdown(
                                        label="Memory Attention", value="default",
                                        choices=["default", "xformers", "flash_attention"])

                                    db_not_cache_latents = gr.Checkbox(label="Don't Cache Latents", value=True)
                                    db_train_text_encoder = gr.Checkbox(label="Train Text Encoder", value=True)
                                    db_use_ema = gr.Checkbox(label="Train EMA", value=False)
                                    db_pad_tokens = gr.Checkbox(label="Pad Tokens", value=True)
                                    db_max_token_length = gr.Dropdown(
                                        label="Max Token Length (Requires Pad Tokens for > 75)", value="75",
                                        choices=["75", "150", "225", "300"])
                                with gr.Column():
                                    gr.HTML("Gradients")
                                    db_gradient_checkpointing = gr.Checkbox(label="Gradient Checkpointing", value=True)
                                    db_gradient_accumulation_steps = gr.Number(label="Gradient Accumulation Steps",
                                                                               precision=0,
                                                                               value=1)
                                    db_max_grad_norm = gr.Number(label="Max Grad Norms", value=1.0, precision=1)

                                with gr.Column():
                                    gr.HTML("Adam Advanced")
                                    db_adam_beta1 = gr.Number(label="Adam Beta 1", precision=1, value=0.9)
                                    db_adam_beta2 = gr.Number(label="Adam Beta 2", precision=3, value=0.999)
                                    db_adam_weight_decay = gr.Number(label="Adam Weight Decay", precision=3, value=0.01)
                                    db_adam_epsilon = gr.Number(label="Adam Epsilon", precision=8, value=0.00000001)

                    with gr.Row():
                        with gr.Column(scale=2):
                            gr.HTML(value="")
                with gr.Tab("Concepts") as concept_tab:
                    with gr.Column(variant="panel"):
                        with gr.Tab("Concept 1"):
                            c1_max_steps, \
                            c1_instance_data_dir, c1_class_data_dir, c1_file_prompt_contents, c1_instance_prompt, \
                            c1_class_prompt, c1_num_class_images, c1_save_sample_prompt, c1_instance_token, \
                            c1_class_token, c1_num_class_images, c1_class_negative_prompt, c1_class_guidance_scale, \
                            c1_class_infer_steps, c1_save_sample_negative_prompt, c1_n_save_sample, c1_sample_seed, \
                            c1_save_guidance_scale, c1_save_infer_steps = build_concept_panel()

                        with gr.Tab("Concept 2"):
                            c2_max_steps, \
                            c2_instance_data_dir, c2_class_data_dir, c2_file_prompt_contents, c2_instance_prompt, \
                            c2_class_prompt, c2_num_class_images, c2_save_sample_prompt, c2_instance_token, \
                            c2_class_token, c2_num_class_images, c2_class_negative_prompt, c2_class_guidance_scale, \
                            c2_class_infer_steps, c2_save_sample_negative_prompt, c2_n_save_sample, c2_sample_seed, \
                            c2_save_guidance_scale, c2_save_infer_steps = build_concept_panel()

                        with gr.Tab("Concept 3"):
                            c3_max_steps, \
                            c3_instance_data_dir, c3_class_data_dir, c3_file_prompt_contents, c3_instance_prompt, \
                            c3_class_prompt, c3_num_class_images, c3_save_sample_prompt, c3_instance_token, \
                            c3_class_token, c3_num_class_images, c3_class_negative_prompt, c3_class_guidance_scale, \
                            c3_class_infer_steps, c3_save_sample_negative_prompt, c3_n_save_sample, c3_sample_seed, \
                            c3_save_guidance_scale, c3_save_infer_steps = build_concept_panel()

                with gr.Tab("Debugging"):
                    with gr.Column():
                        db_generate_sample = gr.Button(value="Generate Sample Image")
                        db_log_memory = gr.Button(value="Log Memory")

            with gr.Column(variant="panel"):
                db_status = gr.HTML(elem_id="db_status", value="")
                db_progress = gr.HTML(elem_id="db_progress", value="")
                db_outcome = gr.HTML(elem_id="db_error", value="")
                db_progressbar = gr.HTML(elem_id="db_progressbar")
                db_gallery = gr.Gallery(label='Output', show_label=False, elem_id='db_gallery').style(grid=4)
                db_preview = gr.Image(elem_id='db_preview', visible=False)
                setup_progressbar(db_progressbar, db_preview, 'db', textinfo=db_progress)

        db_save_params.click(
            fn=DreamboothConfig().save_params,
            inputs=[
                db_model_dir, db_max_train_steps, db_num_train_epochs, db_save_embedding_every, db_save_preview_every,
                db_learning_rate, db_scale_lr, db_lr_scheduler, db_lr_warmup_steps, db_resolution, db_center_crop,
                db_hflip, db_pretrained_vae_name_or_path, db_use_concepts, db_concepts_path,
                db_train_batch_size, db_sample_batch_size, db_use_cpu, db_use_8bit_adam, db_mixed_precision,
                db_attention, db_train_text_encoder, db_use_ema, db_pad_tokens, db_max_token_length,
                db_gradient_checkpointing, db_gradient_accumulation_steps, db_max_grad_norm, db_adam_beta1,
                db_adam_beta2, db_adam_weight_decay, db_adam_epsilon, c1_max_steps, c1_instance_data_dir, c1_class_data_dir,
                c1_file_prompt_contents, c1_instance_prompt, c1_class_prompt, c1_save_sample_prompt, c1_instance_token,
                c1_class_token, c1_num_class_images, c1_class_negative_prompt, c1_class_guidance_scale,
                c1_class_infer_steps, c1_save_sample_negative_prompt, c1_n_save_sample, c1_sample_seed,
                c1_save_guidance_scale, c1_save_infer_steps, c2_max_steps, c2_instance_data_dir, c2_class_data_dir,
                c2_file_prompt_contents, c2_instance_prompt, c2_class_prompt, c2_save_sample_prompt,
                c2_instance_token, c2_class_token, c2_num_class_images, c2_class_negative_prompt,
                c2_class_guidance_scale, c2_class_infer_steps, c2_save_sample_negative_prompt,
                c2_n_save_sample, c2_sample_seed, c2_save_guidance_scale, c2_save_infer_steps, c3_max_steps,
                c3_instance_data_dir, c3_class_data_dir, c3_file_prompt_contents, c3_instance_prompt,
                c3_class_prompt, c3_save_sample_prompt, c3_instance_token, c3_class_token, c3_num_class_images,
                c3_class_negative_prompt, c3_class_guidance_scale, c3_class_infer_steps, c3_save_sample_negative_prompt,
                c3_n_save_sample, c3_sample_seed, c3_save_guidance_scale, c3_save_infer_steps
            ]
        )

        db_create_from_hub.change(
            fn=lambda x: gr_show(x),
            inputs=[db_create_from_hub],
            outputs=[hub_row],
        )

        db_create_from_hub.change(
            fn=lambda x: {
                hub_row: gr_show(x is True),
                local_row: gr_show(x is False)
            },
            inputs=[db_create_from_hub],
            outputs=[
                hub_row,
                local_row
            ]
        )

        db_use_concepts.change(
            fn=lambda x: {
                concept_tab: gr_show(x is True)
            },
            inputs=[db_use_concepts],
            outputs=[
                concept_tab
            ]
        )

        sample_inputs = [
            db_model_dir,
            c1_save_sample_prompt,
            c1_save_sample_negative_prompt,
            c1_sample_seed,
            c1_save_guidance_scale,
            c1_save_infer_steps,
            c1_n_save_sample
        ]

        db_generate_sample.click(
            fn=wrap_gradio_gpu_call(generate_sample_img, extra_outputs=[gr.update()]),
            _js="db_start_progress",
            inputs=sample_inputs,
            outputs=[db_status]
        )

        db_log_memory.click(
            fn=log_memory,
            inputs=[],
            outputs=[db_status]
        )

        db_performance_wizard.click(
            fn=performance_wizard,
            inputs=[],
            outputs=[
                db_status,
                c1_num_class_images,
                db_train_batch_size,
                db_sample_batch_size,
                db_not_cache_latents,
                db_gradient_checkpointing,
                db_use_ema,
                db_train_text_encoder,
                db_mixed_precision,
                db_use_cpu,
                db_use_8bit_adam
            ]
        )

        db_train_wizard_person.click(
            fn=training_wizard_person,
            inputs=[
                db_model_dir,
                db_use_concepts,
                db_concepts_path,
                c1_instance_data_dir,
                c1_class_data_dir,
                db_learning_rate
            ],
            outputs=[
                db_status,
                db_max_train_steps,
                c1_num_class_images
            ]
        )

        db_train_wizard_object.click(
            fn=training_wizard,
            inputs=[
                db_model_dir,
                db_use_concepts,
                db_concepts_path,
                c1_instance_data_dir,
                c1_class_data_dir,
                db_learning_rate
            ],
            outputs=[
                db_status,
                db_max_train_steps,
                c1_num_class_images
            ]
        )

        db_generate_checkpoint.click(
            fn=wrap_gradio_gpu_call(conversion.compile_checkpoint, extra_outputs=[gr.update()]),
            _js="db_start_progress",
            inputs=[
                db_model_dir,
                db_pretrained_vae_name_or_path,
                db_half_model
            ],
            outputs=[
                db_status,
                db_outcome
            ]
        )

        db_create_embedding.click(
            fn=wrap_gradio_gpu_call(conversion.extract_checkpoint, extra_outputs=[gr.update()]),
            _js="db_start_progress",
            inputs=[
                db_new_model_name,
                src_checkpoint,
                diff_type,
                db_new_model_url,
                db_new_model_token
            ],
            outputs=[
                db_model_dir,
                db_status,
                db_outcome,
            ]
        )

        db_train_embedding.click(
            fn=save_and_execute(dreambooth.start_training, extra_outputs=[gr.update()], wrap_gpu=True),
            _js="db_start_progress",
            inputs=[
                db_model_dir
            ],
            outputs=[
                db_status,
                db_outcome,
            ]
        )

        db_load_params.click(
            fn=dreambooth.load_params,
            inputs=[
                db_model_dir
            ],
            outputs=[
                db_half_model,
                db_use_concepts,
                db_pretrained_vae_name_or_path,
                c1_instance_data_dir,
                c1_class_data_dir,
                c1_instance_prompt,
                c1_class_prompt,
                c1_file_prompt_contents,
                c1_instance_token,
                c1_class_token,
                c1_save_sample_prompt,
                c1_save_sample_negative_prompt,
                c1_n_save_sample,
                c1_sample_seed,
                c1_save_guidance_scale,
                c1_save_infer_steps,
                c1_num_class_images,
                db_resolution,
                db_center_crop,
                db_train_text_encoder,
                db_train_batch_size,
                db_sample_batch_size,
                db_num_train_epochs,
                db_max_train_steps,
                db_gradient_accumulation_steps,
                db_gradient_checkpointing,
                db_learning_rate,
                db_scale_lr,
                db_lr_scheduler,
                db_lr_warmup_steps,
                db_attention,
                db_use_8bit_adam,
                db_adam_beta1,
                db_adam_beta2,
                db_adam_weight_decay,
                db_adam_epsilon,
                db_max_grad_norm,
                db_save_preview_every,
                db_save_embedding_every,
                db_mixed_precision,
                db_not_cache_latents,
                db_concepts_path,
                db_use_cpu,
                db_pad_tokens,
                db_max_token_length,
                db_hflip,
                db_use_ema,
                c1_class_negative_prompt,
                c2_class_guidance_scale,
                c3_class_infer_steps,
                db_status
            ]
        )

        db_interrupt_training.click(
            fn=lambda: shared.state.interrupt(),
            inputs=[],
            outputs=[],
        )

    return (dreambooth_interface, "Dreambooth", "dreambooth_interface"),


def build_concept_panel():
    with gr.Column():
        max_steps = gr.Number(label="Maximum Training Steps", value=-1,precision=0)
        gr.HTML(value="Directories")
        instance_data_dir = gr.Textbox(label='Dataset Directory',
                                       placeholder="Path to directory with input images")
        class_data_dir = gr.Textbox(label='Classification Dataset Directory',
                                    placeholder="(Optional) Path to directory with "
                                                "classification/regularization images")
    with gr.Column():
        gr.HTML(value="Prompts")
        instance_prompt = gr.Textbox(label="Instance prompt",
                                     placeholder="Optionally use [filewords] to read image "
                                                 "captions from files.")
        class_prompt = gr.Textbox(label="Class Prompt",
                                  placeholder="Optionally use [filewords] to read image "
                                              "captions from files.")
        class_negative_prompt = gr.Textbox(label="Classification Image Negative Prompt")
        save_sample_prompt = gr.Textbox(label="Sample Image Prompt",
                                        placeholder="Leave blank to use instance prompt. "
                                                    "Optionally use [filewords] to base "
                                                    "sample captions on instance images.")
        save_sample_negative_prompt = gr.Textbox(label="Sample Image Negative Prompt")

    with gr.Column():
        gr.HTML(value="Filewords")
        file_prompt_contents = gr.Dropdown(label="Existing Prompt Contents",
                                           value="Description",
                                           choices=["Description",
                                                    "Instance Token + Description",
                                                    "Class Token + Description",
                                                    "Instance Token + Class Token + Description"])
        instance_token = gr.Textbox(label='Instance Token',
                                    placeholder="When using [filewords], this is the subject to use when building prompts.")
        class_token = gr.Textbox(label='Class Token',
                                 placeholder="When using [filewords], this is the class to use when building prompts.")

    with gr.Column():
        gr.HTML("Image Generation")
        num_class_images = gr.Number(label='Total Number of Class/Reg Images', value=0, precision=0)
        class_guidance_scale = gr.Number(label="Classification CFG Scale", value=7.5, max=12, min=1, precision=2)
        class_infer_steps = gr.Number(label="Classification Steps", value=40, min=10, max=200, precision=0)
        n_save_sample = gr.Number(label="Number of Samples to Generate", value=1, precision=0)
        sample_seed = gr.Number(label="Sample Seed", value=-1, precision=0)
        save_guidance_scale = gr.Number(label="Sample CFG Scale", value=7.5, max=12, min=1, precision=2)
        save_infer_steps = gr.Number(label="Sample Steps", value=40, min=10, max=200, precision=0)
    return [max_steps, instance_data_dir, class_data_dir, file_prompt_contents, instance_prompt, class_prompt, num_class_images,
            save_sample_prompt, instance_token, class_token, num_class_images, class_negative_prompt,
            class_guidance_scale, class_infer_steps, save_sample_negative_prompt, n_save_sample, sample_seed,
            save_guidance_scale, save_infer_steps]


def save_and_execute(func, extra_outputs=None, wrap_gpu=False):
    def f(*args, **kwargs):
        res = func(*args, **kwargs)
        return res

    if wrap_gpu:
        return wrap_gradio_call(f, extra_outputs=extra_outputs, add_stats=True)
    else:
        return wrap_gradio_gpu_call(f, extra_outputs=extra_outputs)


script_callbacks.on_ui_tabs(on_ui_tabs)
