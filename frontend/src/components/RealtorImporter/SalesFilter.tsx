import React, { useState } from 'react';
import './SalesFilter.css';

const SalesFilter = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="sales-filter-container">
      <button className="filter-button" onClick={() => setIsOpen(!isOpen)}>
        Sales in Area
        <span className="arrow-down"></span>
      </button>
      {isOpen && (
        <div className="filter-dropdown">
          <div className="sales-range-header">
            <span>0 Sales</span>
            <span>47+ Sales</span>
          </div>
          <div className="histogram">
            {/* This is a simplified representation of the histogram */}
            <div className="bar" style={{ height: '60%' }}></div>
            <div className="bar" style={{ height: '80%' }}></div>
            <div className="bar" style={{ height: '40%' }}></div>
            <div className="bar" style={{ height: '30%' }}></div>
            <div className="bar" style={{ height: '20%' }}></div>
            <div className="bar" style={{ height: '15%' }}></div>
            <div className="bar" style={{ height: '10%' }}></div>
            <div className="bar" style={{ height: '5%' }}></div>
            <div className="bar" style={{ height: '2%' }}></div>
          </div>
          <div className="range-slider-container">
            <div className="range-slider">
              <div className="slider-track"></div>
              <div className="slider-thumb" style={{ left: '0%' }}></div>
              <div className="slider-thumb" style={{ left: '100%' }}></div>
            </div>
          </div>
          <div className="input-range-container">
            <input type="text" placeholder="Min" className="range-input" />
            <span className="separator">-</span>
            <input type="text" placeholder="Max" className="range-input" />
          </div>
          <div className="dropdown-actions">
            <button className="clear-button">Clear</button>
            <button className="done-button">Done</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesFilter; 