# 🎬 ClipGenius AI - AI-Powered Podcast Clip Generator

Transform long-form podcast videos into viral short-form clips automatically using cutting-edge AI technology.

## 🚀 Features

- **AI-Powered Content Selection**: Uses Google Gemini to identify the most engaging moments
- **Active Speaker Detection**: Computer vision tracks and focuses on who's speaking
- **Vertical Video Generation**: Automatically converts to 9:16 format for social media
- **Professional Subtitles**: AI-generated subtitles with custom styling
- **Cloud Processing**: Built on Modal for scalable GPU-powered processing
- **Multi-Platform Support**: Works with local files and YouTube URLs

## 🛠️ Tech Stack

- **Backend**: FastAPI, Modal (Cloud GPU)
- **AI Models**: WhisperX (Speech-to-Text), Google Gemini (Content Analysis)
- **Computer Vision**: LR-ASD (Active Speaker Detection), OpenCV
- **Video Processing**: FFmpeg, FFmpegCV
- **Cloud Storage**: AWS S3
- **ML Framework**: PyTorch, Transformers

## 📋 Prerequisites

- Python 3.12+
- CUDA-compatible GPU (recommended)
- AWS S3 bucket
- Google Gemini API key
- Modal account

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/clipgenius-ai.git
cd clipgenius-ai
```

### 2. Set Up Virtual Environment
```bash
cd SAAS_Backend
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the `SAAS_Backend` directory:
```env
GOOGLE_GENERATIVEAI_API_KEY=your_gemini_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your_s3_bucket_name
```

### 5. Set Up Modal
```bash
pip install modal
modal token new
```

## 🎯 Usage

### Local Processing
```bash
python main.py --input "path/to/video.mp4" --output_dir "output_clips"
```

### YouTube Processing
```bash
python main.py --input "https://youtube.com/watch?v=VIDEO_ID" --use_youtube --output_dir "output_clips"
```

### Cloud Processing (Modal)
```bash
modal deploy main.py
```

## 📁 Project Structure

```
SAAS!/
├── SAAS_Backend/
│   ├── main.py                 # Main processing pipeline
│   ├── requirements.txt        # Python dependencies
│   ├── LR-ASD/                # Active Speaker Detection
│   │   ├── ASD.py             # ASD model implementation
│   │   ├── Columbia_test.py   # Testing and evaluation
│   │   ├── model/             # Neural network models
│   │   └── weight/            # Pre-trained model weights
│   └── fonts/                 # Custom fonts for subtitles
└── SAAS_frontend/             # Frontend (to be developed)
```

## 🔧 Configuration

### Video Processing Settings
- **Output Resolution**: 1080x1920 (9:16 aspect ratio)
- **Frame Rate**: 25 FPS
- **Audio Sample Rate**: 16kHz
- **Subtitle Font**: Anton (custom styled)

### AI Model Settings
- **WhisperX Model**: large-v2
- **Chunk Duration**: 600 seconds (10 minutes)
- **Clip Duration**: 10-60 seconds
- **Face Detection Scale**: 0.25

## 🎨 Customization

### Subtitle Styling
Edit the `create_subtitles_with_ffmpeg` function in `main.py` to customize:
- Font family and size
- Colors and outline
- Positioning and margins

### Video Processing
Modify `create_vertical_video` function to adjust:
- Output resolution
- Cropping behavior
- Background blur effects

## 📊 Performance

- **Processing Speed**: ~2-3x real-time with GPU
- **Memory Usage**: ~8GB GPU memory recommended
- **Output Quality**: 1080p vertical video with AAC audio

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [WhisperX](https://github.com/m-bain/whisperX) for speech recognition
- [LR-ASD](https://github.com/okankop/LR-ASD) for active speaker detection
- [Modal](https://modal.com) for cloud GPU infrastructure
- [Google Gemini](https://ai.google.dev/) for content analysis

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/clipgenius-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/clipgenius-ai/discussions)
- **Email**: support@clipgenius.ai

---

**Made with ❤️ for content creators** 