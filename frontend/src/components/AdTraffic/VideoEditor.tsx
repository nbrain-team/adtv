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

  const styles = {
    container: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
    },
    leftPanel: {
      background: 'rgba(17, 24, 39, 0.95)',
      backdropFilter: 'blur(10px)',
      borderRight: '1px solid rgba(255, 255, 255, 0.1)'
    },
    rightPanel: {
      background: 'rgba(31, 41, 55, 0.98)',
      backdropFilter: 'blur(10px)'
    },
    videoContainer: {
      background: 'radial-gradient(circle at center, rgba(99, 102, 241, 0.1) 0%, transparent 70%)',
      border: '2px solid rgba(99, 102, 241, 0.2)',
      borderRadius: '16px',
      boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.1)'
    },
    button: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      border: 'none',
      borderRadius: '8px',
      color: 'white',
      padding: '10px 20px',
      fontWeight: '600',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      fontSize: '14px'
    },
    secondaryButton: {
      background: 'rgba(55, 65, 81, 0.5)',
      border: '1px solid rgba(107, 114, 128, 0.3)',
      borderRadius: '8px',
      color: '#e5e7eb',
      padding: '10px 20px',
      fontWeight: '500',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      fontSize: '14px'
    },
    tab: {
      background: 'transparent',
      border: 'none',
      color: '#9ca3af',
      padding: '12px 16px',
      cursor: 'pointer',
      transition: 'all 0.3s ease',
      fontSize: '14px',
      fontWeight: '500',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      borderRadius: '8px',
      margin: '0 4px'
    },
    activeTab: {
      background: 'rgba(99, 102, 241, 0.1)',
      color: '#818cf8',
      borderBottom: 'none'
    },
    slider: {
      width: '100%',
      height: '6px',
      borderRadius: '3px',
      background: 'rgba(107, 114, 128, 0.3)',
      outline: 'none',
      WebkitAppearance: 'none' as any,
      cursor: 'pointer'
    },
    input: {
      background: 'rgba(17, 24, 39, 0.5)',
      border: '1px solid rgba(107, 114, 128, 0.3)',
      borderRadius: '8px',
      color: '#e5e7eb',
      padding: '10px 14px',
      fontSize: '14px',
      width: '100%',
      transition: 'all 0.2s ease'
    },
    select: {
      background: 'rgba(17, 24, 39, 0.5)',
      border: '1px solid rgba(107, 114, 128, 0.3)',
      borderRadius: '8px',
      color: '#e5e7eb',
      padding: '10px 14px',
      fontSize: '14px',
      width: '100%',
      cursor: 'pointer'
    },
    label: {
      color: '#d1d5db',
      fontSize: '13px',
      fontWeight: '500',
      marginBottom: '6px',
      display: 'block',
      letterSpacing: '0.025em'
    },
    effectGroup: {
      background: 'rgba(17, 24, 39, 0.3)',
      borderRadius: '12px',
      padding: '16px',
      marginBottom: '12px',
      border: '1px solid rgba(107, 114, 128, 0.2)'
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex" style={styles.container}>
      {/* Left Panel - Video Preview */}
      <div className="flex-1 flex flex-col" style={styles.leftPanel}>
        {/* Header */}
        <div className="p-5 border-b border-gray-800/50">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-white flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg">
                <Zap className="w-5 h-5 text-white" />
              </div>
              Video Editor Pro
            </h2>
            <div className="flex gap-2">
              <button
                onClick={() => setIsFullscreen(!isFullscreen)}
                style={{...styles.secondaryButton, padding: '8px 12px'}}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(55, 65, 81, 0.8)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(55, 65, 81, 0.5)'}
              >
                {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </button>
              <button
                onClick={handleReset}
                style={styles.secondaryButton}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(55, 65, 81, 0.8)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(55, 65, 81, 0.5)'}
              >
                <RotateCcw className="w-4 h-4 mr-2" style={{ display: 'inline' }} />
                Reset All
              </button>
              <button
                onClick={handleSave}
                style={styles.button}
                onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
              >
                <Save className="w-4 h-4 mr-2" style={{ display: 'inline' }} />
                Save Changes
              </button>
              {onClose && (
                <button
                  onClick={onClose}
                  style={{...styles.secondaryButton, padding: '8px 12px'}}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(55, 65, 81, 0.5)'}
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Video Container */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="relative w-full max-w-4xl" style={styles.videoContainer}>
            {videoLoading && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-lg z-10">
                <div className="text-white">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
                  <p className="mt-4 text-sm">Loading preview...</p>
                </div>
              </div>
            )}
            <video
              ref={videoRef}
              src={previewUrl}
              className="w-full rounded-lg"
              controls
              onLoadedData={() => setVideoLoading(false)}
              onPlay={() => setIsPlaying(true)}
              onPause={() => setIsPlaying(false)}
              style={{ maxHeight: '70vh' }}
            />
          </div>
        </div>

        {/* URL Preview Bar */}
        <div className="p-4 border-t border-gray-800/50">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Preview URL</span>
            <div className="flex-1 bg-gray-900/50 rounded-lg px-3 py-2">
              <code className="text-xs text-purple-400 font-mono break-all">{previewUrl}</code>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Controls */}
      <div className="w-[420px] overflow-y-auto" style={styles.rightPanel}>
        {/* Tabs */}
        <div className="p-4 border-b border-gray-700/50">
          <div className="flex flex-wrap justify-center">
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
                style={{
                  ...styles.tab,
                  ...(activeTab === tab.id ? styles.activeTab : {})
                }}
                onMouseEnter={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.background = 'rgba(55, 65, 81, 0.3)';
                  }
                }}
                onMouseLeave={(e) => {
                  if (activeTab !== tab.id) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {/* Effects Tab */}
          {activeTab === 'effects' && (
            <div className="space-y-4">
              <div style={styles.effectGroup}>
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  Transitions
                </h3>
                <div className="space-y-4">
                  <div>
                    <label style={styles.label}>
                      Fade In
                      <span className="float-right text-purple-400">{effects.fadeIn}s</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="3"
                      step="0.5"
                      value={effects.fadeIn}
                      onChange={(e) => setEffects({...effects, fadeIn: parseFloat(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>

                  <div>
                    <label style={styles.label}>
                      Fade Out
                      <span className="float-right text-purple-400">{effects.fadeOut}s</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="3"
                      step="0.5"
                      value={effects.fadeOut}
                      onChange={(e) => setEffects({...effects, fadeOut: parseFloat(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>
                </div>
              </div>

              <div style={styles.effectGroup}>
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 bg-pink-500 rounded-full"></div>
                  Visual Effects
                </h3>
                <div className="space-y-4">
                  <div>
                    <label style={styles.label}>
                      Blur
                      <span className="float-right text-purple-400">{effects.blur}%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={effects.blur}
                      onChange={(e) => setEffects({...effects, blur: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>

                  <div>
                    <label style={styles.label}>
                      Brightness
                      <span className="float-right text-purple-400">{effects.brightness > 0 ? '+' : ''}{effects.brightness}</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={effects.brightness}
                      onChange={(e) => setEffects({...effects, brightness: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>

                  <div>
                    <label style={styles.label}>
                      Contrast
                      <span className="float-right text-purple-400">{effects.contrast > 0 ? '+' : ''}{effects.contrast}</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={effects.contrast}
                      onChange={(e) => setEffects({...effects, contrast: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>

                  <div>
                    <label style={styles.label}>
                      Saturation
                      <span className="float-right text-purple-400">{effects.saturation > 0 ? '+' : ''}{effects.saturation}</span>
                    </label>
                    <input
                      type="range"
                      min="-100"
                      max="100"
                      value={effects.saturation}
                      onChange={(e) => setEffects({...effects, saturation: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>
                </div>
              </div>

              <div style={styles.effectGroup}>
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  Playback
                </h3>
                <div>
                  <label style={styles.label}>
                    Speed
                    <span className="float-right text-purple-400">{effects.speed}%</span>
                  </label>
                  <input
                    type="range"
                    min="25"
                    max="400"
                    step="25"
                    value={effects.speed}
                    onChange={(e) => setEffects({...effects, speed: parseInt(e.target.value)})}
                    style={styles.slider}
                    className="slider"
                  />
                  <div className="flex justify-between mt-2">
                    <span className="text-xs text-gray-500">Slow</span>
                    <span className="text-xs text-gray-500">Normal</span>
                    <span className="text-xs text-gray-500">Fast</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Text Tab */}
          {activeTab === 'text' && (
            <div style={styles.effectGroup}>
              <div className="space-y-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={textOverlay.enabled}
                    onChange={(e) => setTextOverlay({...textOverlay, enabled: e.target.checked})}
                    className="w-5 h-5 rounded border-gray-600 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-white font-medium">Enable Text Overlay</span>
                </label>

                {textOverlay.enabled && (
                  <div className="space-y-4 mt-4">
                    <div>
                      <label style={styles.label}>Text Content</label>
                      <input
                        type="text"
                        value={textOverlay.text}
                        onChange={(e) => setTextOverlay({...textOverlay, text: e.target.value})}
                        style={styles.input}
                        placeholder="Enter your text..."
                        onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)'}
                        onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(107, 114, 128, 0.3)'}
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label style={styles.label}>Font</label>
                        <select
                          value={textOverlay.font}
                          onChange={(e) => setTextOverlay({...textOverlay, font: e.target.value})}
                          style={styles.select}
                        >
                          <option value="Arial">Arial</option>
                          <option value="Helvetica">Helvetica</option>
                          <option value="Times">Times</option>
                          <option value="Georgia">Georgia</option>
                          <option value="Courier">Courier</option>
                        </select>
                      </div>

                      <div>
                        <label style={styles.label}>Color</label>
                        <select
                          value={textOverlay.color}
                          onChange={(e) => setTextOverlay({...textOverlay, color: e.target.value})}
                          style={styles.select}
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
                      <label style={styles.label}>
                        Size
                        <span className="float-right text-purple-400">{textOverlay.size}px</span>
                      </label>
                      <input
                        type="range"
                        min="20"
                        max="200"
                        value={textOverlay.size}
                        onChange={(e) => setTextOverlay({...textOverlay, size: parseInt(e.target.value)})}
                        style={styles.slider}
                        className="slider"
                      />
                    </div>

                    <div>
                      <label style={styles.label}>Position</label>
                      <select
                        value={textOverlay.position}
                        onChange={(e) => setTextOverlay({...textOverlay, position: e.target.value})}
                        style={styles.select}
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
                      <label style={styles.label}>Background</label>
                      <select
                        value={textOverlay.background}
                        onChange={(e) => setTextOverlay({...textOverlay, background: e.target.value})}
                        style={styles.select}
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
              <h3 className="text-white font-semibold mb-4">Choose a Filter</h3>
              <div className="grid grid-cols-2 gap-3">
                {filters.map(filter => (
                  <button
                    key={filter.id}
                    onClick={() => setActiveFilter(filter.id)}
                    className="relative overflow-hidden rounded-lg transition-all duration-300"
                    style={{
                      padding: '12px',
                      background: activeFilter === filter.id 
                        ? `linear-gradient(135deg, ${filter.color}40, ${filter.color}20)`
                        : 'rgba(17, 24, 39, 0.5)',
                      border: activeFilter === filter.id 
                        ? `2px solid ${filter.color}`
                        : '2px solid transparent',
                      color: activeFilter === filter.id ? '#fff' : '#9ca3af',
                      fontWeight: '500',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => {
                      if (activeFilter !== filter.id) {
                        e.currentTarget.style.background = 'rgba(55, 65, 81, 0.5)';
                        e.currentTarget.style.borderColor = filter.color + '40';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (activeFilter !== filter.id) {
                        e.currentTarget.style.background = 'rgba(17, 24, 39, 0.5)';
                        e.currentTarget.style.borderColor = 'transparent';
                      }
                    }}
                  >
                    {activeFilter === filter.id && (
                      <div 
                        className="absolute inset-0 opacity-20"
                        style={{
                          background: `radial-gradient(circle at center, ${filter.color}, transparent)`
                        }}
                      />
                    )}
                    <span className="relative z-10">{filter.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Overlay Tab */}
          {activeTab === 'overlay' && (
            <div style={styles.effectGroup}>
              <label className="flex items-center gap-3 cursor-pointer mb-4">
                <input
                  type="checkbox"
                  checked={logoOverlay.enabled}
                  onChange={(e) => setLogoOverlay({...logoOverlay, enabled: e.target.checked})}
                  className="w-5 h-5 rounded border-gray-600 text-purple-500 focus:ring-purple-500"
                />
                <span className="text-white font-medium">Enable Logo/Watermark</span>
              </label>

              {logoOverlay.enabled && (
                <div className="space-y-4">
                  <div>
                    <label style={styles.label}>Logo URL or Public ID</label>
                    <input
                      type="text"
                      value={logoOverlay.url}
                      onChange={(e) => setLogoOverlay({...logoOverlay, url: e.target.value})}
                      style={styles.input}
                      placeholder="logo_image_id"
                      onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)'}
                      onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(107, 114, 128, 0.3)'}
                    />
                  </div>

                  <div>
                    <label style={styles.label}>Position</label>
                    <select
                      value={logoOverlay.position}
                      onChange={(e) => setLogoOverlay({...logoOverlay, position: e.target.value})}
                      style={styles.select}
                    >
                      <option value="bottom-right">Bottom Right</option>
                      <option value="bottom-left">Bottom Left</option>
                      <option value="top-right">Top Right</option>
                      <option value="top-left">Top Left</option>
                      <option value="center">Center</option>
                    </select>
                  </div>

                  <div>
                    <label style={styles.label}>
                      Size
                      <span className="float-right text-purple-400">{logoOverlay.size}px</span>
                    </label>
                    <input
                      type="range"
                      min="50"
                      max="500"
                      step="10"
                      value={logoOverlay.size}
                      onChange={(e) => setLogoOverlay({...logoOverlay, size: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>

                  <div>
                    <label style={styles.label}>
                      Opacity
                      <span className="float-right text-purple-400">{logoOverlay.opacity}%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={logoOverlay.opacity}
                      onChange={(e) => setLogoOverlay({...logoOverlay, opacity: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Audio Tab */}
          {activeTab === 'audio' && (
            <div style={styles.effectGroup}>
              <div className="space-y-4">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={audio.muted}
                    onChange={(e) => setAudio({...audio, muted: e.target.checked})}
                    className="w-5 h-5 rounded border-gray-600 text-purple-500 focus:ring-purple-500"
                  />
                  <span className="text-white font-medium">Mute Video</span>
                </label>

                {!audio.muted && (
                  <div>
                    <label style={styles.label}>
                      Volume
                      <span className="float-right text-purple-400">{audio.volume}%</span>
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={audio.volume}
                      onChange={(e) => setAudio({...audio, volume: parseInt(e.target.value)})}
                      style={styles.slider}
                      className="slider"
                    />
                  </div>
                )}

                <div>
                  <label style={styles.label}>Background Music (Audio Public ID)</label>
                  <input
                    type="text"
                    value={audio.backgroundMusic}
                    onChange={(e) => setAudio({...audio, backgroundMusic: e.target.value})}
                    style={styles.input}
                    placeholder="background_music_id"
                    onFocus={(e) => e.currentTarget.style.borderColor = 'rgba(139, 92, 246, 0.5)'}
                    onBlur={(e) => e.currentTarget.style.borderColor = 'rgba(107, 114, 128, 0.3)'}
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

      {/* Custom CSS for sliders */}
      <style>{`
        .slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          transition: transform 0.2s ease;
        }
        
        .slider::-webkit-slider-thumb:hover {
          transform: scale(1.2);
        }
        
        .slider::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        input[type="range"]::-webkit-slider-runnable-track {
          background: linear-gradient(to right, 
            #8b5cf6 0%, 
            #8b5cf6 var(--value), 
            rgba(107, 114, 128, 0.3) var(--value), 
            rgba(107, 114, 128, 0.3) 100%);
        }
      `}</style>
    </div>
  );
};

export default VideoEditor; 