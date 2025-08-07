import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Pause, 
  Download, 
  Save, 
  RotateCcw,
  Type,
  Image,
  Volume2,
  Palette,
  Sparkles,
  Layers,
  Zap
} from 'lucide-react';

interface VideoEditorProps {
  videoUrl: string;
  publicId: string;
  cloudName: string;
  onSave?: (editedUrl: string, transformations: any) => void;
  onClose?: () => void;
}

interface Transformation {
  id: string;
  type: string;
  params: any;
  label: string;
}

const VideoEditor: React.FC<VideoEditorProps> = ({ 
  videoUrl, 
  publicId, 
  cloudName,
  onSave,
  onClose 
}) => {
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [previewUrl, setPreviewUrl] = useState(videoUrl);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState('effects');
  const videoRef = useRef<HTMLVideoElement>(null);

  // Text overlay state
  const [textOverlay, setTextOverlay] = useState({
    enabled: false,
    text: '',
    font: 'Arial',
    size: 60,
    color: 'white',
    position: 'center',
    background: 'none'
  });

  // Effects state
  const [effects, setEffects] = useState({
    fadeIn: 0,
    fadeOut: 0,
    blur: 0,
    brightness: 0,
    contrast: 0,
    saturation: 0,
    speed: 100
  });

  // Filter state
  const [activeFilter, setActiveFilter] = useState('none');

  // Audio state
  const [audio, setAudio] = useState({
    volume: 100,
    muted: false,
    backgroundMusic: ''
  });

  // Logo overlay state
  const [logoOverlay, setLogoOverlay] = useState({
    enabled: false,
    url: '',
    position: 'bottom-right',
    size: 150,
    opacity: 100
  });

  // Build Cloudinary URL with transformations
  const buildTransformationUrl = () => {
    let transformArray = [];

    // Add fade effects
    if (effects.fadeIn > 0) {
      transformArray.push({ effect: `fade:${effects.fadeIn * 1000}` });
    }

    // Add visual effects
    if (effects.blur > 0) {
      transformArray.push({ effect: `blur:${effects.blur * 10}` });
    }
    if (effects.brightness !== 0) {
      transformArray.push({ effect: `brightness:${effects.brightness}` });
    }
    if (effects.contrast !== 0) {
      transformArray.push({ effect: `contrast:${effects.contrast}` });
    }
    if (effects.saturation !== 0) {
      transformArray.push({ effect: `saturation:${effects.saturation}` });
    }

    // Add speed adjustment
    if (effects.speed !== 100) {
      transformArray.push({ effect: `accelerate:${effects.speed}` });
    }

    // Add filters
    if (activeFilter !== 'none') {
      transformArray.push({ effect: activeFilter });
    }

    // Add text overlay
    if (textOverlay.enabled && textOverlay.text) {
      const encodedText = encodeURIComponent(textOverlay.text);
      const textTransform: any = {
        overlay: {
          font_family: textOverlay.font,
          font_size: textOverlay.size,
          text: encodedText
        },
        color: textOverlay.color,
        gravity: textOverlay.position,
        y: 20
      };
      
      if (textOverlay.background !== 'none') {
        textTransform.background = textOverlay.background;
      }
      
      transformArray.push(textTransform);
    }

    // Add logo overlay
    if (logoOverlay.enabled && logoOverlay.url) {
      transformArray.push({
        overlay: logoOverlay.url,
        gravity: logoOverlay.position.replace('-', '_'),
        width: logoOverlay.size,
        opacity: logoOverlay.opacity
      });
    }

    // Add audio transformations
    if (audio.muted) {
      transformArray.push({ volume: 'mute' });
    } else if (audio.volume !== 100) {
      transformArray.push({ volume: audio.volume });
    }

    // Add fade out effect (should be last)
    if (effects.fadeOut > 0) {
      transformArray.push({ effect: `fade:-${effects.fadeOut * 1000}` });
    }

    // Build the URL
    const baseUrl = `https://res.cloudinary.com/${cloudName}/video/upload`;
    const transformString = transformArray.length > 0 
      ? '/' + transformArray.map(t => {
          if (typeof t === 'object') {
            return Object.entries(t).map(([key, value]) => {
              if (typeof value === 'object' && value !== null) {
                return `${key}_${Object.entries(value).map(([k, v]) => `${k}:${v}`).join('_')}`;
              }
              return `${key}_${value}`;
            }).join(',');
          }
          return t;
        }).join('/')
      : '';
    
    return `${baseUrl}${transformString}/${publicId}.mp4`;
  };

  // Update preview when transformations change
  useEffect(() => {
    const newUrl = buildTransformationUrl();
    setPreviewUrl(newUrl);
  }, [textOverlay, effects, activeFilter, audio, logoOverlay]);

  const handlePlayPause = () => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.pause();
      } else {
        videoRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleReset = () => {
    setTextOverlay({
      enabled: false,
      text: '',
      font: 'Arial',
      size: 60,
      color: 'white',
      position: 'center',
      background: 'none'
    });
    setEffects({
      fadeIn: 0,
      fadeOut: 0,
      blur: 0,
      brightness: 0,
      contrast: 0,
      saturation: 0,
      speed: 100
    });
    setActiveFilter('none');
    setAudio({
      volume: 100,
      muted: false,
      backgroundMusic: ''
    });
    setLogoOverlay({
      enabled: false,
      url: '',
      position: 'bottom-right',
      size: 150,
      opacity: 100
    });
  };

  const handleSave = () => {
    if (onSave) {
      const allTransformations = {
        textOverlay,
        effects,
        filter: activeFilter,
        audio,
        logoOverlay
      };
      onSave(previewUrl, allTransformations);
    }
  };

  const filters = [
    { id: 'none', name: 'None' },
    { id: 'sepia', name: 'Sepia' },
    { id: 'grayscale', name: 'Grayscale' },
    { id: 'vignette', name: 'Vignette' },
    { id: 'oil_paint', name: 'Oil Paint' },
    { id: 'cartoonify', name: 'Cartoon' },
    { id: 'outline', name: 'Outline' },
    { id: 'art:zorro', name: 'Artistic' }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-95 z-50 flex">
      {/* Left Panel - Video Preview */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-white">Video Editor</h2>
            <div className="flex gap-2">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600 flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Reset
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-600"
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="relative bg-black rounded-lg overflow-hidden shadow-2xl">
            <video
              ref={videoRef}
              src={previewUrl}
              className="max-w-full max-h-[60vh]"
              controls
            />
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex gap-2">
              <button
                onClick={handlePlayPause}
                className="p-3 bg-blue-600 text-white rounded-full hover:bg-blue-500"
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>

        <div className="p-4 bg-gray-900 text-white text-xs">
          <p>Preview URL: {previewUrl}</p>
        </div>
      </div>

      {/* Right Panel - Controls */}
      <div className="w-96 bg-gray-900 border-l border-gray-800 overflow-y-auto">
        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          {[
            { id: 'effects', label: 'Effects', icon: Sparkles },
            { id: 'text', label: 'Text', icon: Type },
            { id: 'filters', label: 'Filters', icon: Palette },
            { id: 'overlay', label: 'Overlay', icon: Layers },
            { id: 'audio', label: 'Audio', icon: Volume2 }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 py-3 px-4 flex items-center justify-center gap-2 transition-colors ${
                activeTab === tab.id 
                  ? 'bg-gray-800 text-blue-400 border-b-2 border-blue-400' 
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-4 space-y-4">
          {/* Effects Tab */}
          {activeTab === 'effects' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Fade In (seconds)
                </label>
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="0.5"
                  value={effects.fadeIn}
                  onChange={(e) => setEffects({...effects, fadeIn: parseFloat(e.target.value)})}
                  className="w-full"
                />
                <span className="text-xs text-gray-400">{effects.fadeIn}s</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Fade Out (seconds)
                </label>
                <input
                  type="range"
                  min="0"
                  max="3"
                  step="0.5"
                  value={effects.fadeOut}
                  onChange={(e) => setEffects({...effects, fadeOut: parseFloat(e.target.value)})}
                  className="w-full"
                />
                <span className="text-xs text-gray-400">{effects.fadeOut}s</span>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Blur
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={effects.blur}
                  onChange={(e) => setEffects({...effects, blur: parseInt(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Brightness
                </label>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={effects.brightness}
                  onChange={(e) => setEffects({...effects, brightness: parseInt(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Contrast
                </label>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={effects.contrast}
                  onChange={(e) => setEffects({...effects, contrast: parseInt(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Saturation
                </label>
                <input
                  type="range"
                  min="-100"
                  max="100"
                  value={effects.saturation}
                  onChange={(e) => setEffects({...effects, saturation: parseInt(e.target.value)})}
                  className="w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Speed
                </label>
                <input
                  type="range"
                  min="25"
                  max="400"
                  step="25"
                  value={effects.speed}
                  onChange={(e) => setEffects({...effects, speed: parseInt(e.target.value)})}
                  className="w-full"
                />
                <span className="text-xs text-gray-400">{effects.speed}%</span>
              </div>
            </>
          )}

          {/* Text Tab */}
          {activeTab === 'text' && (
            <>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                  <input
                    type="checkbox"
                    checked={textOverlay.enabled}
                    onChange={(e) => setTextOverlay({...textOverlay, enabled: e.target.checked})}
                  />
                  Enable Text Overlay
                </label>
              </div>

              {textOverlay.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Text
                    </label>
                    <input
                      type="text"
                      value={textOverlay.text}
                      onChange={(e) => setTextOverlay({...textOverlay, text: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                      placeholder="Enter your text..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Font
                    </label>
                    <select
                      value={textOverlay.font}
                      onChange={(e) => setTextOverlay({...textOverlay, font: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                    >
                      <option value="Arial">Arial</option>
                      <option value="Helvetica">Helvetica</option>
                      <option value="Times">Times</option>
                      <option value="Georgia">Georgia</option>
                      <option value="Courier">Courier</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Size
                    </label>
                    <input
                      type="range"
                      min="20"
                      max="200"
                      value={textOverlay.size}
                      onChange={(e) => setTextOverlay({...textOverlay, size: parseInt(e.target.value)})}
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Color
                    </label>
                    <select
                      value={textOverlay.color}
                      onChange={(e) => setTextOverlay({...textOverlay, color: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                    >
                      <option value="white">White</option>
                      <option value="black">Black</option>
                      <option value="red">Red</option>
                      <option value="blue">Blue</option>
                      <option value="green">Green</option>
                      <option value="yellow">Yellow</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Position
                    </label>
                    <select
                      value={textOverlay.position}
                      onChange={(e) => setTextOverlay({...textOverlay, position: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                    >
                      <option value="center">Center</option>
                      <option value="north">Top</option>
                      <option value="south">Bottom</option>
                      <option value="east">Right</option>
                      <option value="west">Left</option>
                      <option value="north_east">Top Right</option>
                      <option value="north_west">Top Left</option>
                      <option value="south_east">Bottom Right</option>
                      <option value="south_west">Bottom Left</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Background
                    </label>
                    <select
                      value={textOverlay.background}
                      onChange={(e) => setTextOverlay({...textOverlay, background: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                    >
                      <option value="none">None</option>
                      <option value="rgb:00000080">Semi-transparent Black</option>
                      <option value="rgb:FFFFFF80">Semi-transparent White</option>
                      <option value="black">Solid Black</option>
                      <option value="white">Solid White</option>
                    </select>
                  </div>
                </>
              )}
            </>
          )}

          {/* Filters Tab */}
          {activeTab === 'filters' && (
            <div className="grid grid-cols-2 gap-3">
              {filters.map(filter => (
                <button
                  key={filter.id}
                  onClick={() => setActiveFilter(filter.id)}
                  className={`p-3 rounded text-sm ${
                    activeFilter === filter.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {filter.name}
                </button>
              ))}
            </div>
          )}

          {/* Overlay Tab */}
          {activeTab === 'overlay' && (
            <>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                  <input
                    type="checkbox"
                    checked={logoOverlay.enabled}
                    onChange={(e) => setLogoOverlay({...logoOverlay, enabled: e.target.checked})}
                  />
                  Enable Logo/Watermark
                </label>
              </div>

              {logoOverlay.enabled && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Logo URL or Public ID
                    </label>
                    <input
                      type="text"
                      value={logoOverlay.url}
                      onChange={(e) => setLogoOverlay({...logoOverlay, url: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                      placeholder="logo_image_id"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Position
                    </label>
                    <select
                      value={logoOverlay.position}
                      onChange={(e) => setLogoOverlay({...logoOverlay, position: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                    >
                      <option value="bottom-right">Bottom Right</option>
                      <option value="bottom-left">Bottom Left</option>
                      <option value="top-right">Top Right</option>
                      <option value="top-left">Top Left</option>
                      <option value="center">Center</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Size
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="500"
                      step="10"
                      value={logoOverlay.size}
                      onChange={(e) => setLogoOverlay({...logoOverlay, size: parseInt(e.target.value)})}
                      className="w-full"
                    />
                    <span className="text-xs text-gray-400">{logoOverlay.size}px</span>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Opacity
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={logoOverlay.opacity}
                      onChange={(e) => setLogoOverlay({...logoOverlay, opacity: parseInt(e.target.value)})}
                      className="w-full"
                    />
                    <span className="text-xs text-gray-400">{logoOverlay.opacity}%</span>
                  </div>
                </>
              )}
            </>
          )}

          {/* Audio Tab */}
          {activeTab === 'audio' && (
            <>
              <div>
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
                  <input
                    type="checkbox"
                    checked={audio.muted}
                    onChange={(e) => setAudio({...audio, muted: e.target.checked})}
                  />
                  Mute Video
                </label>
              </div>

              {!audio.muted && (
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Volume
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={audio.volume}
                    onChange={(e) => setAudio({...audio, volume: parseInt(e.target.value)})}
                    className="w-full"
                  />
                  <span className="text-xs text-gray-400">{audio.volume}%</span>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Background Music (Audio Public ID)
                </label>
                <input
                  type="text"
                  value={audio.backgroundMusic}
                  onChange={(e) => setAudio({...audio, backgroundMusic: e.target.value})}
                  className="w-full px-3 py-2 bg-gray-800 text-white rounded"
                  placeholder="background_music_id"
                />
                <p className="text-xs text-gray-400 mt-1">
                  Upload audio files to Cloudinary first
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoEditor; 