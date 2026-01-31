'use client'

import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, Loader2 } from 'lucide-react'
import clsx from 'clsx'

interface FileUploadProps {
  onUpload: (file: File) => void
  isLoading: boolean
  compact?: boolean
}

export default function FileUpload({ onUpload, isLoading, compact = false }: FileUploadProps) {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0])
    }
  }, [onUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
    },
    multiple: false,
    disabled: isLoading,
  })

  if (compact) {
    return (
      <div
        {...getRootProps()}
        className={clsx(
          'flex items-center gap-3 px-4 py-3 bg-white border border-gray-200 rounded-lg cursor-pointer transition-colors',
          isDragActive && 'border-primary-500 bg-primary-50',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        {isLoading ? (
          <Loader2 className="w-5 h-5 text-primary-500 spinner" />
        ) : (
          <Upload className="w-5 h-5 text-gray-400" />
        )}
        <span className="text-sm text-gray-600">
          {isDragActive ? 'Drop CSV here' : 'Upload another CSV'}
        </span>
      </div>
    )
  }

  return (
    <div
      {...getRootProps()}
      className={clsx(
        'flex flex-col items-center justify-center p-12 bg-white border-2 border-dashed rounded-xl cursor-pointer transition-all',
        isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-gray-400',
        isLoading && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      
      <div className={clsx(
        'p-4 rounded-full mb-4',
        isDragActive ? 'bg-primary-100' : 'bg-gray-100'
      )}>
        {isLoading ? (
          <Loader2 className="w-8 h-8 text-primary-500 spinner" />
        ) : (
          <FileText className={clsx(
            'w-8 h-8',
            isDragActive ? 'text-primary-500' : 'text-gray-400'
          )} />
        )}
      </div>

      <h3 className="text-lg font-medium text-gray-900 mb-1">
        {isDragActive ? 'Drop your CSV file' : 'Upload a CSV file'}
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        Drag and drop or click to browse
      </p>

      <div className="flex items-center gap-6 text-xs text-gray-400">
        <span>CSV format</span>
        <span>Max 50MB</span>
        <span>Headers required</span>
      </div>
    </div>
  )
}
