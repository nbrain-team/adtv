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
  X
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
    { id: 'none', name: 'None' },
    { id: 'sepia', name: 'Sepia' },
    { id: 'grayscale', name: 'B&W' },
    { id: 'vignette', name: 'Vignette' },
    { id: 'oil_paint', name: 'Oil Paint' },
    { id: 'cartoonify', name: 'Cartoon' },
    { id: 'outline', name: 'Outline' },
    { id: 'art:zorro', name: 'Artistic' }
  ];

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.95)',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Header */}
      <div 
        style={{
          backgroundColor: '#1f2937',
          borderBottom: '1px solid #374151',
          padding: '1rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <h2 style={{ color: 'white', fontSize: '1.25rem', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
          <Zap style={{ width: '20px', height: '20px', color: '#a855f7' }} />
          Video Editor
        </h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            onClick={handleReset}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#374151',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <RotateCcw style={{ width: '16px', height: '16px' }} />
            Reset All
          </button>
          <button
            onClick={handleSave}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#7c3aed',
              color: 'white',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
          >
            <Save style={{ width: '16px', height: '16px' }} />
            Save Changes
          </button>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                padding: '0.5rem',
                backgroundColor: '#374151',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer'
              }}
            >
              <X style={{ width: '20px', height: '20px' }} />
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Video Preview - Left Side */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#111827' }}>
          {/* Video Container */}
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
            <div style={{ position: 'relative', width: '100%', maxWidth: '1200px', maxHeight: '80vh' }}>
              {videoLoading && (
                <div style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  color: 'white',
                  textAlign: 'center'
                }}>
                  <div style={{
                    width: '48px',
                    height: '48px',
                    border: '3px solid #374151',
                    borderTopColor: '#a855f7',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite',
                    margin: '0 auto'
                  }} />
                  <p style={{ marginTop: '1rem', fontSize: '0.875rem' }}>Loading preview...</p>
                </div>
              )}
              <video
                ref={videoRef}
                src={previewUrl}
                style={{
                  width: '100%',
                  height: 'auto',
                  maxHeight: '70vh',
                  backgroundColor: 'black',
                  borderRadius: '0.5rem'
                }}
                controls
                onLoadedData={() => setVideoLoading(false)}
                onPlay={() => setIsPlaying(true)}
                onPause={() => setIsPlaying(false)}
              />
            </div>
          </div>

          {/* URL Preview Bar */}
          <div style={{
            backgroundColor: '#1f2937',
            borderTop: '1px solid #374151',
            padding: '0.75rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem'
          }}>
            <span style={{ color: '#9ca3af', fontSize: '0.75rem', fontWeight: '600', textTransform: 'uppercase' }}>
              Preview URL
            </span>
            <div style={{
              flex: 1,
              backgroundColor: '#111827',
              borderRadius: '0.25rem',
              padding: '0.5rem 0.75rem',
              overflowX: 'auto'
            }}>
              <code style={{ color: '#a855f7', fontSize: '0.75rem', fontFamily: 'monospace', whiteSpace: 'nowrap' }}>
                {previewUrl}
              </code>
            </div>
          </div>
        </div>

        {/* Controls - Right Sidebar */}
        <div style={{ width: '400px', backgroundColor: '#1f2937', borderLeft: '1px solid #374151', display: 'flex', flexDirection: 'column' }}>
          {/* Tabs */}
          <div style={{ borderBottom: '1px solid #374151', display: 'flex' }}>
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
                  flex: 1,
                  padding: '0.75rem',
                  backgroundColor: activeTab === tab.id ? '#374151' : 'transparent',
                  color: activeTab === tab.id ? '#a855f7' : '#9ca3af',
                  border: 'none',
                  borderBottom: activeTab === tab.id ? '2px solid #a855f7' : 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  fontSize: '0.875rem'
                }}
              >
                <tab.icon style={{ width: '16px', height: '16px' }} />
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '1.5rem' }}>
            {/* Effects Tab */}
            {activeTab === 'effects' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                  <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Transitions</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Fade In: {effects.fadeIn}s
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="3"
                        step="0.5"
                        value={effects.fadeIn}
                        onChange={(e) => setEffects({...effects, fadeIn: parseFloat(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Fade Out: {effects.fadeOut}s
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="3"
                        step="0.5"
                        value={effects.fadeOut}
                        onChange={(e) => setEffects({...effects, fadeOut: parseFloat(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                  <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Visual Effects</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Blur: {effects.blur}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={effects.blur}
                        onChange={(e) => setEffects({...effects, blur: parseInt(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Brightness: {effects.brightness > 0 ? '+' : ''}{effects.brightness}
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={effects.brightness}
                        onChange={(e) => setEffects({...effects, brightness: parseInt(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Contrast: {effects.contrast > 0 ? '+' : ''}{effects.contrast}
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={effects.contrast}
                        onChange={(e) => setEffects({...effects, contrast: parseInt(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Saturation: {effects.saturation > 0 ? '+' : ''}{effects.saturation}
                      </label>
                      <input
                        type="range"
                        min="-100"
                        max="100"
                        value={effects.saturation}
                        onChange={(e) => setEffects({...effects, saturation: parseInt(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                  </div>
                </div>

                <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                  <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Playback</h3>
                  <div>
                    <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                      Speed: {effects.speed}%
                    </label>
                    <input
                      type="range"
                      min="25"
                      max="400"
                      step="25"
                      value={effects.speed}
                      onChange={(e) => setEffects({...effects, speed: parseInt(e.target.value)})}
                      style={{ width: '100%' }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Text Tab */}
            {activeTab === 'text' && (
              <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Text Overlay</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                      Enable Text Overlay
                    </label>
                    <input
                      type="checkbox"
                      checked={textOverlay.enabled}
                      onChange={(e) => setTextOverlay({...textOverlay, enabled: e.target.checked})}
                      style={{ width: '16px', height: '16px', accentColor: '#a855f7' }}
                    />
                  </div>

                  {textOverlay.enabled && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Text Content</label>
                        <input
                          type="text"
                          value={textOverlay.text}
                          onChange={(e) => setTextOverlay({...textOverlay, text: e.target.value})}
                          style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
                          placeholder="Enter your text..."
                        />
                      </div>

                      <div style={{ display: 'flex', gap: '0.75rem' }}>
                        <div style={{ flex: 1 }}>
                          <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Font</label>
                          <select
                            value={textOverlay.font}
                            onChange={(e) => setTextOverlay({...textOverlay, font: e.target.value})}
                            style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
                          >
                            <option value="Arial">Arial</option>
                            <option value="Helvetica">Helvetica</option>
                            <option value="Times">Times</option>
                            <option value="Georgia">Georgia</option>
                            <option value="Courier">Courier</option>
                          </select>
                        </div>

                        <div style={{ flex: 1 }}>
                          <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Color</label>
                          <select
                            value={textOverlay.color}
                            onChange={(e) => setTextOverlay({...textOverlay, color: e.target.value})}
                            style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
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
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Size: {textOverlay.size}px
                        </label>
                        <input
                          type="range"
                          min="20"
                          max="200"
                          value={textOverlay.size}
                          onChange={(e) => setTextOverlay({...textOverlay, size: parseInt(e.target.value)})}
                          style={{ width: '100%' }}
                        />
                      </div>

                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Position</label>
                        <select
                          value={textOverlay.position}
                          onChange={(e) => setTextOverlay({...textOverlay, position: e.target.value})}
                          style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
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
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Background</label>
                        <select
                          value={textOverlay.background}
                          onChange={(e) => setTextOverlay({...textOverlay, background: e.target.value})}
                          style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
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
              <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Choose a Filter</h3>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                  {filters.map(filter => (
                    <button
                      key={filter.id}
                      onClick={() => setActiveFilter(filter.id)}
                      style={{
                        padding: '0.75rem',
                        backgroundColor: activeFilter === filter.id ? '#7c3aed' : '#374151',
                        color: activeFilter === filter.id ? 'white' : '#d1d5db',
                        border: 'none',
                        borderRadius: '0.5rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                    >
                      {filter.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Overlay Tab */}
            {activeTab === 'overlay' && (
              <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Logo/Watermark</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                      Enable Logo/Watermark
                    </label>
                    <input
                      type="checkbox"
                      checked={logoOverlay.enabled}
                      onChange={(e) => setLogoOverlay({...logoOverlay, enabled: e.target.checked})}
                      style={{ width: '16px', height: '16px', accentColor: '#a855f7' }}
                    />
                  </div>

                  {logoOverlay.enabled && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Logo URL or Public ID</label>
                        <input
                          type="text"
                          value={logoOverlay.url}
                          onChange={(e) => setLogoOverlay({...logoOverlay, url: e.target.value})}
                          style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
                          placeholder="logo_image_id"
                        />
                      </div>

                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Position</label>
                        <select
                          value={logoOverlay.position}
                          onChange={(e) => setLogoOverlay({...logoOverlay, position: e.target.value})}
                          style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
                        >
                          <option value="bottom-right">Bottom Right</option>
                          <option value="bottom-left">Bottom Left</option>
                          <option value="top-right">Top Right</option>
                          <option value="top-left">Top Left</option>
                          <option value="center">Center</option>
                        </select>
                      </div>

                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Size: {logoOverlay.size}px
                        </label>
                        <input
                          type="range"
                          min="50"
                          max="500"
                          step="10"
                          value={logoOverlay.size}
                          onChange={(e) => setLogoOverlay({...logoOverlay, size: parseInt(e.target.value)})}
                          style={{ width: '100%' }}
                        />
                      </div>

                      <div>
                        <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Opacity: {logoOverlay.opacity}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={logoOverlay.opacity}
                          onChange={(e) => setLogoOverlay({...logoOverlay, opacity: parseInt(e.target.value)})}
                          style={{ width: '100%' }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Audio Tab */}
            {activeTab === 'audio' && (
              <div style={{ backgroundColor: 'rgba(55, 65, 81, 0.5)', borderRadius: '0.5rem', padding: '1rem' }}>
                <h3 style={{ color: 'white', fontSize: '0.875rem', fontWeight: '500', marginBottom: '1rem' }}>Audio</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                      Mute Video
                    </label>
                    <input
                      type="checkbox"
                      checked={audio.muted}
                      onChange={(e) => setAudio({...audio, muted: e.target.checked})}
                      style={{ width: '16px', height: '16px', accentColor: '#a855f7' }}
                    />
                  </div>

                  {!audio.muted && (
                    <div>
                      <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Volume: {audio.volume}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={audio.volume}
                        onChange={(e) => setAudio({...audio, volume: parseInt(e.target.value)})}
                        style={{ width: '100%' }}
                      />
                    </div>
                  )}

                  <div>
                    <label style={{ color: '#d1d5db', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Background Music (Audio Public ID)</label>
                    <input
                      type="text"
                      value={audio.backgroundMusic}
                      onChange={(e) => setAudio({...audio, backgroundMusic: e.target.value})}
                      style={{ width: '100%', padding: '0.5rem 0.75rem', backgroundColor: '#263238', color: 'white', border: '1px solid #4b5563', borderRadius: '0.375rem' }}
                      placeholder="background_music_id"
                    />
                    <p style={{ color: '#9ca3af', fontSize: '0.75rem', marginTop: '0.5rem' }}>
                      Upload audio files to Cloudinary first
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add animation keyframes */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default VideoEditor; 