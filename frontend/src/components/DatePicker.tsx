import React from 'react';
import { TextField } from '@radix-ui/themes';
import { CalendarIcon } from '@radix-ui/react-icons';

interface DatePickerProps {
  selected: Date;
  onChange: (date: Date) => void;
  minDate?: Date;
  maxDate?: Date;
  placeholder?: string;
}

export const DatePicker: React.FC<DatePickerProps> = ({
  selected,
  onChange,
  minDate,
  maxDate,
  placeholder = "Select date"
}) => {
  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0]; // YYYY-MM-DD format
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDate = new Date(e.target.value);
    if (!isNaN(newDate.getTime())) {
      onChange(newDate);
    }
  };

  return (
    <TextField.Root
      type="date"
      value={formatDate(selected)}
      onChange={handleChange}
      min={minDate ? formatDate(minDate) : undefined}
      max={maxDate ? formatDate(maxDate) : undefined}
      placeholder={placeholder}
    >
      <TextField.Slot>
        <CalendarIcon height="16" width="16" />
      </TextField.Slot>
    </TextField.Root>
  );
}; 