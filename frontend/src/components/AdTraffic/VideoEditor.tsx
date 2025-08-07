import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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
  X,
  Eye,
  Scissors
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
  const navigate = useNavigate();
  const [transformations, setTransformations] = useState<Transformation[]>([]);
  const [previewUrl, setPreviewUrl] = useState(videoUrl);
  const [originalUrl] = useState(videoUrl);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState('trim');
  const [videoLoading, setVideoLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
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

  // Trim state
  const [trim, setTrim] = useState({
    enabled: false,
    startTime: 0,
    endTime: 0,
    duration: 0
  });

  // Build Cloudinary URL with transformations
  const buildTransformationUrl = () => {
    let transformArray = [];

    // Add trim transformation first
    if (trim.enabled) {
      let trimTransform = [];
      if (trim.startTime > 0) {
        trimTransform.push(`so_${trim.startTime}`);
      }
      if (trim.endTime > 0) {
        trimTransform.push(`eo_${trim.endTime}`);
      }
      if (trimTransform.length > 0) {
        transformArray.push(trimTransform.join(','));
      }
    }

    // Add fade in effect
    if (effects.fadeIn > 0) {
      transformArray.push(`e_fade:${Math.round(effects.fadeIn * 1000)}`);
    }

    // Add visual effects as a single transformation
    let visualEffects = [];
    if (effects.blur > 0) {
      visualEffects.push(`e_blur:${Math.round(effects.blur * 10)}`);
    }
    if (effects.brightness !== 0) {
      visualEffects.push(`e_brightness:${effects.brightness}`);
    }
    if (effects.contrast !== 0) {
      visualEffects.push(`e_contrast:${effects.contrast}`);
    }
    if (effects.saturation !== 0) {
      visualEffects.push(`e_saturation:${effects.saturation}`);
    }
    if (visualEffects.length > 0) {
      transformArray.push(visualEffects.join(','));
    }

    // Add speed adjustment
    if (effects.speed !== 100) {
      transformArray.push(`e_accelerate:${effects.speed}`);
    }

    // Add filters
    if (activeFilter !== 'none' && activeFilter !== '') {
      // Special handling for art filters
      if (activeFilter.startsWith('art:')) {
        transformArray.push(`e_art:${activeFilter.split(':')[1]}`);
      } else {
        transformArray.push(`e_${activeFilter}`);
      }
    }

    // Add text overlay
    if (textOverlay.enabled && textOverlay.text) {
      const encodedText = encodeURIComponent(textOverlay.text);
      let textTransform = `l_text:${textOverlay.font}_${textOverlay.size}:${encodedText}`;
      textTransform += `,co_${textOverlay.color}`;
      textTransform += `,g_${textOverlay.position}`;
      
      if (textOverlay.background !== 'none') {
        textTransform += `,b_${textOverlay.background}`;
      }
      
      transformArray.push(textTransform);
    }

    // Add logo overlay
    if (logoOverlay.enabled && logoOverlay.url) {
      let logoTransform = `l_${logoOverlay.url}`;
      logoTransform += `,g_${logoOverlay.position.replace('-', '_')}`;
      logoTransform += `,w_${logoOverlay.size}`;
      logoTransform += `,o_${logoOverlay.opacity}`;
      transformArray.push(logoTransform);
    }

    // Add audio transformations
    if (audio.muted) {
      transformArray.push('e_volume:mute');
    } else if (audio.volume !== 100) {
      transformArray.push(`e_volume:${audio.volume}`);
    }

    // Add fade out effect (should be near the end)
    if (effects.fadeOut > 0) {
      transformArray.push(`e_fade:-${Math.round(effects.fadeOut * 1000)}`);
    }

    // Build the URL with slashes between transformation layers
    const baseUrl = `https://res.cloudinary.com/${cloudName}/video/upload`;
    const transformString = transformArray.length > 0 ? '/' + transformArray.join('/') : '';
    
    console.log('Built transformation URL:', `${baseUrl}${transformString}/${publicId}`);
    return `${baseUrl}${transformString}/${publicId}`;
  };

  // Preview changes function
  const handlePreviewChanges = () => {
    const newUrl = buildTransformationUrl();
    setPreviewUrl(newUrl);
    setShowPreview(true);
    setVideoLoading(true);
    
    // Force video reload
    if (videoRef.current) {
      videoRef.current.load();
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
    setTrim({
      enabled: false,
      startTime: 0,
      endTime: 0,
      duration: 0
    });
    setPreviewUrl(originalUrl);
    setShowPreview(false);
  };

  const handleSave = () => {
    if (onSave) {
      const finalUrl = buildTransformationUrl();
      const allTransformations = {
        textOverlay,
        effects,
        filter: activeFilter,
        audio,
        logoOverlay,
        trim
      };
      onSave(finalUrl, allTransformations);
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
        backgroundColor: 'rgba(0, 0, 0, 0.5)',
        zIndex: 9999,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      {/* Modal Container */}
      <div style={{
        backgroundColor: 'white',
        margin: '2rem auto',
        width: '95%',
        maxWidth: '1600px',
        height: 'calc(100% - 4rem)',
        borderRadius: '0.75rem',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div 
          style={{
            backgroundColor: 'white',
            borderBottom: '1px solid #e5e7eb',
            padding: '1rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <img 
              src="/new-icons/adtv-logo.png" 
              alt="ADTV Logo" 
              style={{ 
                height: '35px', 
                cursor: 'pointer',
                transition: 'opacity 0.2s'
              }}
              onClick={() => navigate('/ad-traffic')}
              onMouseEnter={(e) => e.currentTarget.style.opacity = '0.8'}
              onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
            />
            <h2 style={{ 
              color: '#111827', 
              fontSize: '1.25rem', 
              fontWeight: '600', 
              margin: 0,
              paddingLeft: '1rem',
              borderLeft: '2px solid #e5e7eb'
            }}>
              Video Editor
            </h2>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={handlePreviewChanges}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#059669'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#10b981'}
            >
              <Eye style={{ width: '16px', height: '16px' }} />
              Preview Changes
            </button>
            <button
              onClick={handleReset}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#4b5563'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#6b7280'}
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
                gap: '0.5rem',
                fontSize: '0.875rem',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#6d28d9'}
              onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#7c3aed'}
            >
              <Save style={{ width: '16px', height: '16px' }} />
              Save Changes
            </button>
            {onClose && (
              <button
                onClick={onClose}
                style={{
                  padding: '0.5rem',
                  backgroundColor: '#f3f4f6',
                  color: '#6b7280',
                  border: '1px solid #e5e7eb',
                  borderRadius: '0.375rem',
                  cursor: 'pointer'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e5e7eb';
                  e.currentTarget.style.color = '#374151';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3f4f6';
                  e.currentTarget.style.color = '#6b7280';
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
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', backgroundColor: '#f9fafb', minWidth: 0 }}>
            {/* Video Container */}
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '2rem', overflow: 'hidden' }}>
              <div style={{ position: 'relative', width: '100%', maxWidth: '1200px', maxHeight: '80vh' }}>
                {videoLoading && (
                  <div style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: '#6b7280',
                    textAlign: 'center',
                    zIndex: 10
                  }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      border: '3px solid #e5e7eb',
                      borderTopColor: '#7c3aed',
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
                    borderRadius: '0.5rem',
                    display: 'block',
                    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)'
                  }}
                  controls
                  onLoadedData={() => setVideoLoading(false)}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onError={(e) => {
                    console.error('Video error:', e);
                    setVideoLoading(false);
                  }}
                />
              </div>
            </div>

            {/* Status Bar */}
            <div style={{
              backgroundColor: 'white',
              borderTop: '1px solid #e5e7eb',
              padding: '0.75rem 1.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.75rem',
              flexShrink: 0
            }}>
              <span style={{ 
                color: showPreview ? '#10b981' : '#6b7280', 
                fontSize: '0.75rem', 
                fontWeight: '600', 
                textTransform: 'uppercase' 
              }}>
                {showPreview ? 'Preview Mode' : 'Original Video'}
              </span>
              <div style={{
                flex: 1,
                backgroundColor: '#f9fafb',
                borderRadius: '0.25rem',
                padding: '0.5rem 0.75rem',
                overflowX: 'auto',
                maxWidth: 'calc(100% - 150px)',
                border: '1px solid #e5e7eb'
              }}>
                <code style={{ 
                  color: '#7c3aed', 
                  fontSize: '0.75rem', 
                  fontFamily: 'monospace', 
                  whiteSpace: 'nowrap',
                  display: 'block'
                }}>
                  {previewUrl}
                </code>
              </div>
            </div>
          </div>

          {/* Controls - Right Sidebar */}
          <div style={{ 
            width: '420px', 
            minWidth: '420px',
            maxWidth: '420px',
            backgroundColor: 'white', 
            borderLeft: '1px solid #e5e7eb', 
            display: 'flex', 
            flexDirection: 'column',
            overflow: 'visible'
          }}>
            {/* Tabs */}
            <div style={{ 
              borderBottom: '1px solid #e5e7eb', 
              display: 'flex', 
              flexShrink: 0, 
              backgroundColor: '#f9fafb',
              overflowX: 'auto',
              minHeight: '48px'
            }}>
              {[
                { id: 'trim', label: 'Trim', icon: Scissors },
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
                    flex: '0 0 auto',
                    minWidth: '80px',
                    padding: '0.75rem 0.5rem',
                    backgroundColor: activeTab === tab.id ? 'white' : 'transparent',
                    color: activeTab === tab.id ? '#7c3aed' : '#6b7280',
                    border: 'none',
                    borderBottom: activeTab === tab.id ? '2px solid #7c3aed' : 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.25rem',
                    fontSize: '0.8rem',
                    fontWeight: activeTab === tab.id ? '500' : '400',
                    whiteSpace: 'nowrap'
                  }}
                >
                  <tab.icon style={{ width: '14px', height: '14px', flexShrink: 0 }} />
                  <span>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* Tab Content */}
            <div style={{ 
              flex: 1, 
              overflowY: 'auto', 
              overflowX: 'visible',
              padding: '1rem',
              backgroundColor: 'white',
              width: '100%'
            }}>
              {/* Trim Tab */}
              {activeTab === 'trim' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                    <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', margin: 0, marginBottom: '1rem' }}>Video Trimming</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <label style={{ 
                          color: '#4b5563', 
                          fontSize: '0.875rem', 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '0.5rem', 
                          cursor: 'pointer',
                          width: 'fit-content'
                        }}>
                          <input
                            type="checkbox"
                            checked={trim.enabled}
                            onChange={(e) => setTrim({...trim, enabled: e.target.checked})}
                            style={{ 
                              width: '16px', 
                              height: '16px', 
                              accentColor: '#7c3aed',
                              flexShrink: 0
                            }}
                          />
                          <span>Enable Video Trimming</span>
                        </label>
                      </div>

                      {trim.enabled && (
                        <>
                          <div>
                            <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                              Start Time: {trim.startTime}s
                            </label>
                            <input
                              type="range"
                              min="0"
                              max="60"
                              step="0.5"
                              value={trim.startTime}
                              onChange={(e) => setTrim({...trim, startTime: parseFloat(e.target.value)})}
                              style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                            />
                            <input
                              type="number"
                              min="0"
                              max="60"
                              step="0.5"
                              value={trim.startTime}
                              onChange={(e) => setTrim({...trim, startTime: parseFloat(e.target.value) || 0})}
                              style={{ 
                                width: '100%', 
                                marginTop: '0.5rem',
                                padding: '0.5rem 0.75rem', 
                                backgroundColor: '#f9fafb', 
                                color: '#111827', 
                                border: '1px solid #e5e7eb', 
                                borderRadius: '0.375rem',
                                boxSizing: 'border-box',
                                fontSize: '0.875rem'
                              }}
                              placeholder="Start time in seconds"
                            />
                          </div>

                          <div>
                            <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                              End Time: {trim.endTime > 0 ? trim.endTime + 's' : 'Original End'}
                            </label>
                            <input
                              type="range"
                              min="0"
                              max="60"
                              step="0.5"
                              value={trim.endTime}
                              onChange={(e) => setTrim({...trim, endTime: parseFloat(e.target.value)})}
                              style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                            />
                            <input
                              type="number"
                              min="0"
                              max="60"
                              step="0.5"
                              value={trim.endTime}
                              onChange={(e) => setTrim({...trim, endTime: parseFloat(e.target.value) || 0})}
                              style={{ 
                                width: '100%', 
                                marginTop: '0.5rem',
                                padding: '0.5rem 0.75rem', 
                                backgroundColor: '#f9fafb', 
                                color: '#111827', 
                                border: '1px solid #e5e7eb', 
                                borderRadius: '0.375rem',
                                boxSizing: 'border-box',
                                fontSize: '0.875rem'
                              }}
                              placeholder="End time in seconds (0 = original end)"
                            />
                          </div>

                          <div style={{ 
                            padding: '0.75rem', 
                            backgroundColor: 'white', 
                            borderRadius: '0.375rem',
                            border: '1px solid #e5e7eb'
                          }}>
                            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
                              <strong>Tips:</strong><br />
                              • Set start time to remove content from the beginning<br />
                              • Set end time to remove content from the end<br />
                              • Leave end time at 0 to keep original ending<br />
                              • Times are in seconds (e.g., 5.5 = 5½ seconds)
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Effects Tab */}
              {activeTab === 'effects' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                  <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                    <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Transitions</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Fade In: {effects.fadeIn}s
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="3"
                          step="0.5"
                          value={effects.fadeIn}
                          onChange={(e) => setEffects({...effects, fadeIn: parseFloat(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Fade Out: {effects.fadeOut}s
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="3"
                          step="0.5"
                          value={effects.fadeOut}
                          onChange={(e) => setEffects({...effects, fadeOut: parseFloat(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                    <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Visual Effects</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Blur: {effects.blur}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={effects.blur}
                          onChange={(e) => setEffects({...effects, blur: parseInt(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Brightness: {effects.brightness > 0 ? '+' : ''}{effects.brightness}
                        </label>
                        <input
                          type="range"
                          min="-100"
                          max="100"
                          value={effects.brightness}
                          onChange={(e) => setEffects({...effects, brightness: parseInt(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Contrast: {effects.contrast > 0 ? '+' : ''}{effects.contrast}
                        </label>
                        <input
                          type="range"
                          min="-100"
                          max="100"
                          value={effects.contrast}
                          onChange={(e) => setEffects({...effects, contrast: parseInt(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                      <div>
                        <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                          Saturation: {effects.saturation > 0 ? '+' : ''}{effects.saturation}
                        </label>
                        <input
                          type="range"
                          min="-100"
                          max="100"
                          value={effects.saturation}
                          onChange={(e) => setEffects({...effects, saturation: parseInt(e.target.value)})}
                          style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                    <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Playback</h3>
                    <div>
                      <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                        Speed: {effects.speed}%
                      </label>
                      <input
                        type="range"
                        min="25"
                        max="400"
                        step="25"
                        value={effects.speed}
                        onChange={(e) => setEffects({...effects, speed: parseInt(e.target.value)})}
                        style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Text Tab */}
              {activeTab === 'text' && (
                <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                  <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Text Overlay</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={textOverlay.enabled}
                          onChange={(e) => setTextOverlay({...textOverlay, enabled: e.target.checked})}
                          style={{ width: '16px', height: '16px', accentColor: '#7c3aed' }}
                        />
                        Enable Text Overlay
                      </label>
                    </div>

                    {textOverlay.enabled && (
                      <>
                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Text Content</label>
                          <input
                            type="text"
                            value={textOverlay.text}
                            onChange={(e) => setTextOverlay({...textOverlay, text: e.target.value})}
                            style={{ 
                              width: '100%', 
                              padding: '0.5rem 0.75rem', 
                              backgroundColor: '#f9fafb', 
                              color: '#111827', 
                              border: '1px solid #e5e7eb', 
                              borderRadius: '0.375rem',
                              boxSizing: 'border-box'
                            }}
                            placeholder="Enter your text..."
                          />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                          <div>
                            <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Font</label>
                            <select
                              value={textOverlay.font}
                              onChange={(e) => setTextOverlay({...textOverlay, font: e.target.value})}
                              style={{ 
                                width: '100%', 
                                padding: '0.5rem 0.75rem', 
                                backgroundColor: '#f9fafb', 
                                color: '#111827', 
                                border: '1px solid #e5e7eb', 
                                borderRadius: '0.375rem',
                                cursor: 'pointer'
                              }}
                            >
                              <option value="Arial">Arial</option>
                              <option value="Helvetica">Helvetica</option>
                              <option value="Times">Times</option>
                              <option value="Georgia">Georgia</option>
                              <option value="Courier">Courier</option>
                            </select>
                          </div>

                          <div>
                            <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Color</label>
                            <select
                              value={textOverlay.color}
                              onChange={(e) => setTextOverlay({...textOverlay, color: e.target.value})}
                              style={{ 
                                width: '100%', 
                                padding: '0.5rem 0.75rem', 
                                backgroundColor: '#f9fafb', 
                                color: '#111827', 
                                border: '1px solid #e5e7eb', 
                                borderRadius: '0.375rem',
                                cursor: 'pointer'
                              }}
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
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                            Size: {textOverlay.size}px
                          </label>
                          <input
                            type="range"
                            min="20"
                            max="200"
                            value={textOverlay.size}
                            onChange={(e) => setTextOverlay({...textOverlay, size: parseInt(e.target.value)})}
                            style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                          />
                        </div>

                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Position</label>
                          <select
                            value={textOverlay.position}
                            onChange={(e) => setTextOverlay({...textOverlay, position: e.target.value})}
                            style={{ 
                              width: '100%', 
                              padding: '0.5rem 0.75rem', 
                              backgroundColor: '#f9fafb', 
                              color: '#111827', 
                              border: '1px solid #e5e7eb', 
                              borderRadius: '0.375rem',
                              cursor: 'pointer'
                            }}
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
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Filters Tab */}
              {activeTab === 'filters' && (
                <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                  <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Choose a Filter</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                    {filters.map(filter => (
                      <button
                        key={filter.id}
                        onClick={() => setActiveFilter(filter.id)}
                        style={{
                          padding: '0.75rem',
                          backgroundColor: activeFilter === filter.id ? '#7c3aed' : 'white',
                          color: activeFilter === filter.id ? 'white' : '#4b5563',
                          border: activeFilter === filter.id ? '1px solid #7c3aed' : '1px solid #e5e7eb',
                          borderRadius: '0.5rem',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          fontSize: '0.875rem'
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
                <div style={{ backgroundColor: '#f9fafb', borderRadius: '0.5rem', padding: '1rem', border: '1px solid #e5e7eb' }}>
                  <h3 style={{ color: '#111827', fontSize: '0.875rem', fontWeight: '600', marginBottom: '1rem' }}>Logo/Watermark</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    <div>
                      <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                          type="checkbox"
                          checked={logoOverlay.enabled}
                          onChange={(e) => setLogoOverlay({...logoOverlay, enabled: e.target.checked})}
                          style={{ width: '16px', height: '16px', accentColor: '#7c3aed' }}
                        />
                        Enable Logo/Watermark
                      </label>
                    </div>

                    {logoOverlay.enabled && (
                      <>
                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Logo URL or Public ID</label>
                          <input
                            type="text"
                            value={logoOverlay.url}
                            onChange={(e) => setLogoOverlay({...logoOverlay, url: e.target.value})}
                            style={{ 
                              width: '100%', 
                              padding: '0.5rem 0.75rem', 
                              backgroundColor: '#f9fafb', 
                              color: '#111827', 
                              border: '1px solid #e5e7eb', 
                              borderRadius: '0.375rem',
                              boxSizing: 'border-box'
                            }}
                            placeholder="logo_image_id"
                          />
                        </div>

                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>Position</label>
                          <select
                            value={logoOverlay.position}
                            onChange={(e) => setLogoOverlay({...logoOverlay, position: e.target.value})}
                            style={{ 
                              width: '100%', 
                              padding: '0.5rem 0.75rem', 
                              backgroundColor: '#f9fafb', 
                              color: '#111827', 
                              border: '1px solid #e5e7eb', 
                              borderRadius: '0.375rem',
                              cursor: 'pointer'
                            }}
                          >
                            <option value="bottom-right">Bottom Right</option>
                            <option value="bottom-left">Bottom Left</option>
                            <option value="top-right">Top Right</option>
                            <option value="top-left">Top Left</option>
                            <option value="center">Center</option>
                          </select>
                        </div>

                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                            Size: {logoOverlay.size}px
                          </label>
                          <input
                            type="range"
                            min="50"
                            max="500"
                            step="10"
                            value={logoOverlay.size}
                            onChange={(e) => setLogoOverlay({...logoOverlay, size: parseInt(e.target.value)})}
                            style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                          />
                        </div>

                        <div>
                          <label style={{ color: '#4b5563', fontSize: '0.875rem', display: 'block', marginBottom: '0.5rem' }}>
                            Opacity: {logoOverlay.opacity}%
                          </label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={logoOverlay.opacity}
                            onChange={(e) => setLogoOverlay({...logoOverlay, opacity: parseInt(e.target.value)})}
                            style={{ width: '100%', cursor: 'pointer', accentColor: '#7c3aed' }}
                          />
                        </div>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Audio Tab */}
              {activeTab === 'audio' && (
                <div style={{ 
                  backgroundColor: '#f9fafb', 
                  borderRadius: '0.5rem', 
                  padding: '1rem', 
                  border: '1px solid #e5e7eb',
                  width: '100%',
                  boxSizing: 'border-box'
                }}>
                  <h3 style={{ 
                    color: '#111827', 
                    fontSize: '0.875rem', 
                    fontWeight: '600', 
                    margin: 0,
                    marginBottom: '1rem'
                  }}>Audio</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', width: '100%' }}>
                    <div>
                      <label style={{ 
                        color: '#4b5563', 
                        fontSize: '0.875rem', 
                        display: 'flex', 
                        alignItems: 'center', 
                        gap: '0.5rem', 
                        cursor: 'pointer',
                        width: 'fit-content'
                      }}>
                        <input
                          type="checkbox"
                          checked={audio.muted}
                          onChange={(e) => setAudio({...audio, muted: e.target.checked})}
                          style={{ 
                            width: '16px', 
                            height: '16px', 
                            accentColor: '#7c3aed',
                            flexShrink: 0
                          }}
                        />
                        <span>Mute Video</span>
                      </label>
                    </div>

                    {!audio.muted && (
                      <div style={{ width: '100%' }}>
                        <label style={{ 
                          color: '#4b5563', 
                          fontSize: '0.875rem', 
                          display: 'block', 
                          marginBottom: '0.5rem',
                          wordWrap: 'break-word'
                        }}>
                          Volume: {audio.volume}%
                        </label>
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={audio.volume}
                          onChange={(e) => setAudio({...audio, volume: parseInt(e.target.value)})}
                          style={{ 
                            width: '100%', 
                            cursor: 'pointer', 
                            accentColor: '#7c3aed',
                            boxSizing: 'border-box'
                          }}
                        />
                      </div>
                    )}

                    <div style={{ width: '100%' }}>
                      <label style={{ 
                        color: '#4b5563', 
                        fontSize: '0.875rem', 
                        display: 'block', 
                        marginBottom: '0.5rem',
                        wordWrap: 'break-word'
                      }}>
                        Background Music (Audio Public ID)
                      </label>
                      <input
                        type="text"
                        value={audio.backgroundMusic}
                        onChange={(e) => setAudio({...audio, backgroundMusic: e.target.value})}
                        style={{ 
                          width: '100%', 
                          padding: '0.5rem 0.75rem', 
                          backgroundColor: '#f9fafb', 
                          color: '#111827', 
                          border: '1px solid #e5e7eb', 
                          borderRadius: '0.375rem',
                          boxSizing: 'border-box',
                          fontSize: '0.875rem'
                        }}
                        placeholder="background_music_id"
                      />
                      <p style={{ 
                        color: '#9ca3af', 
                        fontSize: '0.75rem', 
                        margin: 0,
                        marginTop: '0.5rem',
                        wordWrap: 'break-word'
                      }}>
                        Upload audio files to Cloudinary first
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
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