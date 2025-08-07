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
  Zap,
  X,
  Maximize2,
  Minimize2
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
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [videoLoading, setVideoLoading] = useState(true);
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
    setVideoLoading(true);
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
    { id: 'none', name: 'None', color: '#6b7280' },
    { id: 'sepia', name: 'Sepia', color: '#92400e' },
    { id: 'grayscale', name: 'B&W', color: '#374151' },
    { id: 'vignette', name: 'Vignette', color: '#1f2937' },
    { id: 'oil_paint', name: 'Oil Paint', color: '#7c3aed' },
    { id: 'cartoonify', name: 'Cartoon', color: '#ec4899' },
    { id: 'outline', name: 'Outline', color: '#0891b2' },
    { id: 'art:zorro', name: 'Artistic', color: '#dc2626' }
  ];

  return (
    <div className="fixed inset-0 z-50 flex bg-gray-900">
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-gray-900">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-500" />
              Video Editor
            </h2>
            <div className="flex gap-2">
              <button
                onClick={handleReset}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                Reset All
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Changes
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Video Container - Full size */}
        <div className="flex-1 flex items-center justify-center p-8 bg-gray-900">
          <div className="relative w-full h-full max-w-6xl max-h-[80vh] bg-black rounded-lg overflow-hidden shadow-2xl">
            {videoLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 z-10">
                <div className="text-white text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
                  <p className="mt-4 text-sm">Loading preview...</p>
                </div>
              </div>
            )}
            <video
              ref={videoRef}
              src={previewUrl}
              className="w-full h-full object-contain"
              controls
              onLoadedData={() => setVideoLoading(false)}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
            />
          </div>
        </div>

        {/* URL Preview Bar */}
        <div className="bg-gray-800 border-t border-gray-700 p-3">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-gray-400 uppercase">Preview URL</span>
            <div className="flex-1 bg-gray-900 rounded px-3 py-2 overflow-x-auto">
              <code className="text-xs text-purple-400 font-mono whitespace-nowrap">{previewUrl}</code>
            </div>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Controls */}
      <div className="w-[400px] bg-gray-800 border-l border-gray-700 flex flex-col">
        {/* Tabs */}
        <div className="border-b border-gray-700">
          <div className="flex">
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
                    ? 'bg-gray-700 text-purple-400 border-b-2 border-purple-400' 
                    : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                <span className="text-sm">{tab.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Effects Tab */}
          {activeTab === 'effects' && (
            <div className="space-y-6">
              <div className="bg-gray-700/50 rounded-lg p-4">
                <h3 className="text-white font-medium mb-4">Transitions</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Fade In: {effects.fadeIn}s
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
                  </div>

                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Fade Out: {effects.fadeOut}s
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
                  </div>
                </div>
              </div>

              <div className="bg-gray-700/50 rounded-lg p-4">
                <h3 className="text-white font-medium mb-4">Visual Effects</h3>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Blur: {effects.blur}%
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
                    <label className="text-sm text-gray-300 block mb-2">
                      Brightness: {effects.brightness > 0 ? '+' : ''}{effects.brightness}
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
                    <label className="text-sm text-gray-300 block mb-2">
                      Contrast: {effects.contrast > 0 ? '+' : ''}{effects.contrast}
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
                    <label className="text-sm text-gray-300 block mb-2">
                      Saturation: {effects.saturation > 0 ? '+' : ''}{effects.saturation}
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
                </div>
              </div>

              <div className="bg-gray-700/50 rounded-lg p-4">
                <h3 className="text-white font-medium mb-4">Playback</h3>
                <div>
                  <label className="text-sm text-gray-300 block mb-2">
                    Speed: {effects.speed}%
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
                </div>
              </div>
            </div>
          )}

          {/* Text Tab */}
          {activeTab === 'text' && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="space-y-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={textOverlay.enabled}
                    onChange={(e) => setTextOverlay({...textOverlay, enabled: e.target.checked})}
                    className="w-4 h-4 text-purple-500"
                  />
                  <span className="text-white font-medium">Enable Text Overlay</span>
                </label>

                {textOverlay.enabled && (
                  <div className="space-y-4 mt-4">
                    <div>
                      <label className="text-sm text-gray-300 block mb-2">Text Content</label>
                      <input
                        type="text"
                        value={textOverlay.text}
                        onChange={(e) => setTextOverlay({...textOverlay, text: e.target.value})}
                        className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500"
                        placeholder="Enter your text..."
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-sm text-gray-300 block mb-2">Font</label>
                        <select
                          value={textOverlay.font}
                          onChange={(e) => setTextOverlay({...textOverlay, font: e.target.value})}
                          className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600"
                        >
                          <option value="Arial">Arial</option>
                          <option value="Helvetica">Helvetica</option>
                          <option value="Times">Times</option>
                          <option value="Georgia">Georgia</option>
                          <option value="Courier">Courier</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-sm text-gray-300 block mb-2">Color</label>
                        <select
                          value={textOverlay.color}
                          onChange={(e) => setTextOverlay({...textOverlay, color: e.target.value})}
                          className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600"
                        >
                          <option value="white">White</option>
                          <option value="black">Black</option>
                          <option value="red">Red</option>
                          <option value="blue">Blue</option>
                          <option value="green">Green</option>
                          <option value="yellow">Yellow</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm text-gray-300 block mb-2">
                        Size: {textOverlay.size}px
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
                      <label className="text-sm text-gray-300 block mb-2">Position</label>
                      <select
                        value={textOverlay.position}
                        onChange={(e) => setTextOverlay({...textOverlay, position: e.target.value})}
                        className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600"
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
                      <label className="text-sm text-gray-300 block mb-2">Background</label>
                      <select
                        value={textOverlay.background}
                        onChange={(e) => setTextOverlay({...textOverlay, background: e.target.value})}
                        className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600"
                      >
                        <option value="none">None</option>
                        <option value="rgb:00000080">Semi-transparent Black</option>
                        <option value="rgb:FFFFFF80">Semi-transparent White</option>
                        <option value="black">Solid Black</option>
                        <option value="white">Solid White</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Filters Tab */}
          {activeTab === 'filters' && (
            <div>
              <h3 className="text-white font-medium mb-4">Choose a Filter</h3>
              <div className="grid grid-cols-2 gap-3">
                {filters.map(filter => (
                  <button
                    key={filter.id}
                    onClick={() => setActiveFilter(filter.id)}
                    className={`p-3 rounded-lg transition-all ${
                      activeFilter === filter.id
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {filter.name}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Overlay Tab */}
          {activeTab === 'overlay' && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <label className="flex items-center gap-2 cursor-pointer mb-4">
                <input
                  type="checkbox"
                  checked={logoOverlay.enabled}
                  onChange={(e) => setLogoOverlay({...logoOverlay, enabled: e.target.checked})}
                  className="w-4 h-4 text-purple-500"
                />
                <span className="text-white font-medium">Enable Logo/Watermark</span>
              </label>

              {logoOverlay.enabled && (
                <div className="space-y-4">
                  <div>
                    <label className="text-sm text-gray-300 block mb-2">Logo URL or Public ID</label>
                    <input
                      type="text"
                      value={logoOverlay.url}
                      onChange={(e) => setLogoOverlay({...logoOverlay, url: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500"
                      placeholder="logo_image_id"
                    />
                  </div>

                  <div>
                    <label className="text-sm text-gray-300 block mb-2">Position</label>
                    <select
                      value={logoOverlay.position}
                      onChange={(e) => setLogoOverlay({...logoOverlay, position: e.target.value})}
                      className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600"
                    >
                      <option value="bottom-right">Bottom Right</option>
                      <option value="bottom-left">Bottom Left</option>
                      <option value="top-right">Top Right</option>
                      <option value="top-left">Top Left</option>
                      <option value="center">Center</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Size: {logoOverlay.size}px
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
                  </div>

                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Opacity: {logoOverlay.opacity}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={logoOverlay.opacity}
                      onChange={(e) => setLogoOverlay({...logoOverlay, opacity: parseInt(e.target.value)})}
                      className="w-full"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Audio Tab */}
          {activeTab === 'audio' && (
            <div className="bg-gray-700/50 rounded-lg p-4">
              <div className="space-y-4">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={audio.muted}
                    onChange={(e) => setAudio({...audio, muted: e.target.checked})}
                    className="w-4 h-4 text-purple-500"
                  />
                  <span className="text-white font-medium">Mute Video</span>
                </label>

                {!audio.muted && (
                  <div>
                    <label className="text-sm text-gray-300 block mb-2">
                      Volume: {audio.volume}%
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={audio.volume}
                      onChange={(e) => setAudio({...audio, volume: parseInt(e.target.value)})}
                      className="w-full"
                    />
                  </div>
                )}

                <div>
                  <label className="text-sm text-gray-300 block mb-2">Background Music (Audio Public ID)</label>
                  <input
                    type="text"
                    value={audio.backgroundMusic}
                    onChange={(e) => setAudio({...audio, backgroundMusic: e.target.value})}
                    className="w-full px-3 py-2 bg-gray-800 text-white rounded border border-gray-600 focus:border-purple-500"
                    placeholder="background_music_id"
                  />
                  <p className="text-xs text-gray-500 mt-2">
                    Upload audio files to Cloudinary first
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VideoEditor; 