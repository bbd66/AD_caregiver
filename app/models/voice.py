import os
import queue
import threading
from pathlib import Path
import sounddevice as sd
import vosk
from openai import OpenAI
from playsound import playsound

class VoiceService:
    def __init__(self, api_key, base_url):
        self.tts_api_key = api_key
        self.tts_base_url = base_url
        self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        self.custom_voices = {}
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.load_voice_config()
        self.init_voice_recognition()

    def init_voice_recognition(self):
        """初始化语音识别模型"""
        model_path = "vosk-model-small-cn-0.22"
        if not os.path.exists(model_path):
            raise FileNotFoundError("未找到语音模型文件")
            
        self.model = vosk.Model(model_path)
        self.samplerate = 16000
        self.recognizer = vosk.KaldiRecognizer(self.model, self.samplerate)

    def generate_speech(self, text):
        """生成语音"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            speech_file = Path(__file__).parent / f"speech_{timestamp}.mp3"
            
            client = OpenAI(
                api_key=self.tts_api_key,
                base_url=self.tts_base_url
            )
            
            with client.audio.speech.with_streaming_response.create(
                model="FunAudioLLM/CosyVoice2-0.5B",
                voice=self.current_voice,
                input=text,
                response_format="mp3"
            ) as response:
                response.stream_to_file(speech_file)

            threading.Thread(
                target=self.play_audio,
                args=(str(speech_file),),
                daemon=True
            ).start()
            
        except Exception as e:
            raise Exception(f"语音生成失败: {str(e)}")

    def play_audio(self, file_path):
        """播放音频"""
        try:
            playsound(file_path)
        except Exception as e:
            raise Exception(f"音频播放失败: {str(e)}")

    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.audio_queue.queue.clear()
        threading.Thread(target=self.record_audio).start()

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False

    def record_audio(self):
        """录音线程"""
        try:  
            with sd.RawInputStream(
                samplerate=self.samplerate,
                blocksize=8000,
                dtype='int16',
                channels=1,
                callback=self.audio_callback
            ):
             while self.is_recording:
                sd.sleep(100)
            
            self.process_audio()
            
        except Exception as e:
            raise Exception(f"录音错误: {str(e)}")

    def audio_callback(self, indata, frames, time, status):
        """音频采集回调"""
        if status:
            print(status)
        self.audio_queue.put(bytes(indata))

    def process_audio(self):
        """处理录音结果"""
        audio_data = b''.join(list(self.audio_queue.queue))
        
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get('text', '')
            return text
        return ""

    def load_voice_config(self):
        """加载音色配置"""
        config_path = Path(__file__).parent / "voice_config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.custom_voices = json.load(f)

    def save_voice_config(self):
        """保存音色配置"""
        config_path = Path(__file__).parent / "voice_config.json"
        with open(config_path, 'w') as f:
            json.dump(self.custom_voices, f)

    def update_voice(self, voice_name):
        """更新当前音色"""
        if voice_name == "alex":
            self.current_voice = "FunAudioLLM/CosyVoice2-0.5B:alex"
        else:
            self.current_voice = self.custom_voices.get(voice_name, "alex")
