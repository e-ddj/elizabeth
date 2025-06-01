import React, { useState } from 'react';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

const JobFileUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [jobData, setJobData] = useState(null);
  const [error, setError] = useState(null);

  // Handle file selection
  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setJobData(null);
  };

  // Upload file to Supabase
  const uploadFile = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    try {
      setUploading(true);
      setError(null);

      // Create a unique file name using timestamp and original file name
      const timestamp = new Date().getTime();
      const fileExt = file.name.split('.').pop();
      const filePath = `job-uploads/${timestamp}_${file.name}`;

      // Upload to Supabase storage
      const { data, error: uploadError } = await supabase.storage
        .from('jobs')
        .upload(filePath, file);

      if (uploadError) {
        throw new Error(`Error uploading file: ${uploadError.message}`);
      }

      // Once uploaded, extract job data from the file
      await extractJobData(filePath);

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  // Extract job data from uploaded file
  const extractJobData = async (filePath) => {
    try {
      setExtracting(true);
      setError(null);

      // Call our API to extract job data
      const response = await fetch('http://localhost:5000/api/job-extractor/extract-from-file', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ file_path: filePath }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.description || 'Error extracting job data');
      }

      const data = await response.json();
      setJobData(data);
    } catch (err) {
      console.error('Extraction error:', err);
      setError(err.message);
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="job-file-upload">
      <h2>Upload Job Description File</h2>
      <p>Upload a PDF, DOCX, or TXT file containing a job description.</p>
      
      <div className="upload-section">
        <input 
          type="file" 
          onChange={handleFileChange} 
          accept=".pdf,.docx,.txt"
          disabled={uploading || extracting}
        />
        <button 
          onClick={uploadFile} 
          disabled={!file || uploading || extracting}
        >
          {uploading ? 'Uploading...' : extracting ? 'Extracting...' : 'Upload & Extract'}
        </button>
      </div>
      
      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
        </div>
      )}
      
      {jobData && (
        <div className="job-data-results">
          <h3>Extracted Job Information</h3>
          <div className="job-data-container">
            <pre>{JSON.stringify(jobData, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default JobFileUpload; 