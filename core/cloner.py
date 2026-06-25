import torch
import torchaudio
from chatterbox.tts import ChatterboxTTS


class KokoClone:
    def __init__(self):
        self.model = ChatterboxTTS.from_pretrained(device="cuda" if torch.cuda.is_available() else "cpu")

    def generate(self, text: str, lang: str = "en",
                 reference_audio: str = None, output_path: str = "/tmp/output.wav"):
        if reference_audio:
            wav = self.model.generate(
                text=text,
                audio_prompt_path=reference_audio,
                exaggeration=0.3,
                cfg_weight=0.3,
            )
        else:
            wav = self.model.generate(
                text=text,
                exaggeration=0.3,
                cfg_weight=0.3,
            )
        torchaudio.save(output_path, wav, self.model.sr)
        return output_path
