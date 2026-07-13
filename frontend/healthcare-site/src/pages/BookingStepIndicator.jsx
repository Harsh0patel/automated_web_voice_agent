import React from 'react';

const STEPS = ['Service', 'Doctor', 'Date & Time', 'Details', 'Confirm'];

export default function BookingStepIndicator({ currentStep }) {
  return (
    <div className="booking__steps">
      {STEPS.map((label, i) => {
        const stepNum = i + 1;
        return (
          <div
            key={i}
            className={`booking__step ${
              stepNum === currentStep ? 'booking__step--active' : ''
            } ${stepNum < currentStep ? 'booking__step--done' : ''}`}
          >
            <div className="booking__step-circle">
              {stepNum < currentStep ? '✓' : stepNum}
            </div>
            <span className="booking__step-label">{label}</span>
          </div>
        );
      })}
    </div>
  );
}
