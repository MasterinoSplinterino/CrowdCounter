'use client'

import { useState, useRef } from 'react'
import { Upload, Image as ImageIcon, Video, Loader2, Users, Clock, X } from 'lucide-react'

interface Detection {
  bbox: number[]
  confidence: number
}

interface TestResult {
  count: number
  detections: Detection[]
  image_base64: string
  inference_ms: number
}

export default function TestPage() {
  const [mode, setMode] = useState<'image' | 'video'>('image')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [imageResult, setImageResult] = useState<TestResult | null>(null)
  const [videoResults, setVideoResults] = useState<TestResult[]>([])
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0)
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0])
    }
  }

  const handleFile = async (file: File) => {
    setError(null)
    setImageResult(null)
    setVideoResults([])
    setCurrentFrameIndex(0)

    const isImage = file.type.startsWith('image/')
    const isVideo = file.type.startsWith('video/')

    if (!isImage && !isVideo) {
      setError('Please upload an image or video file')
      return
    }

    setMode(isImage ? 'image' : 'video')
    setLoading(true)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const endpoint = isImage ? '/api/test/image' : '/api/test/video'
      const res = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(err.detail || `HTTP ${res.status}`)
      }

      const data = await res.json()

      if (isImage) {
        setImageResult(data as TestResult)
      } else {
        setVideoResults(data as TestResult[])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to process file')
    } finally {
      setLoading(false)
    }
  }

  const clearResults = () => {
    setImageResult(null)
    setVideoResults([])
    setCurrentFrameIndex(0)
    setError(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const currentResult = mode === 'image' ? imageResult : videoResults[currentFrameIndex]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Test Detection
        </h1>
        {(imageResult || videoResults.length > 0) && (
          <button
            onClick={clearResults}
            className="flex items-center gap-2 px-4 py-2 text-sm text-gray-600 dark:text-gray-300 hover:text-red-500 dark:hover:text-red-400 transition-colors"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Upload Area */}
      {!imageResult && videoResults.length === 0 && (
        <div
          className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
            dragActive
              ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,video/*"
            onChange={handleFileInput}
            className="hidden"
          />

          {loading ? (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
              <p className="text-gray-600 dark:text-gray-300">Processing...</p>
            </div>
          ) : (
            <>
              <Upload className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-lg text-gray-600 dark:text-gray-300 mb-2">
                Drag and drop a file here, or{' '}
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-blue-500 hover:text-blue-600 font-medium"
                >
                  browse
                </button>
              </p>
              <p className="text-sm text-gray-400">
                Supports images (JPG, PNG, WebP) and videos (MP4, WebM)
              </p>
            </>
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Results */}
      {currentResult && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Image Preview */}
          <div className="lg:col-span-2">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm overflow-hidden">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {mode === 'image' ? (
                    <ImageIcon className="w-5 h-5 text-gray-400" />
                  ) : (
                    <Video className="w-5 h-5 text-gray-400" />
                  )}
                  <span className="font-medium text-gray-900 dark:text-white">
                    {mode === 'image' ? 'Detection Result' : `Frame ${currentFrameIndex + 1} of ${videoResults.length}`}
                  </span>
                </div>
              </div>
              <div className="relative">
                <img
                  src={currentResult.image_base64}
                  alt="Detection result"
                  className="w-full h-auto"
                />
              </div>
            </div>

            {/* Video Frame Navigation */}
            {videoResults.length > 1 && (
              <div className="mt-4 flex items-center gap-4">
                <button
                  onClick={() => setCurrentFrameIndex(Math.max(0, currentFrameIndex - 1))}
                  disabled={currentFrameIndex === 0}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Previous
                </button>
                <div className="flex-1">
                  <input
                    type="range"
                    min={0}
                    max={videoResults.length - 1}
                    value={currentFrameIndex}
                    onChange={(e) => setCurrentFrameIndex(parseInt(e.target.value))}
                    className="w-full"
                  />
                </div>
                <button
                  onClick={() => setCurrentFrameIndex(Math.min(videoResults.length - 1, currentFrameIndex + 1))}
                  disabled={currentFrameIndex === videoResults.length - 1}
                  className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </div>

          {/* Stats */}
          <div className="space-y-4">
            {/* People Count */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                  <Users className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">People Detected</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">
                    {currentResult.count}
                  </p>
                </div>
              </div>
            </div>

            {/* Inference Time */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                  <Clock className="w-6 h-6 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">Inference Time</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white">
                    {currentResult.inference_ms.toFixed(0)}
                    <span className="text-lg font-normal text-gray-400 ml-1">ms</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Detections List */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
              <h3 className="font-medium text-gray-900 dark:text-white mb-4">
                Detections ({currentResult.detections.length})
              </h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {currentResult.detections.map((det, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between py-2 px-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm"
                  >
                    <span className="text-gray-600 dark:text-gray-300">
                      Person {i + 1}
                    </span>
                    <span className="font-mono text-gray-500 dark:text-gray-400">
                      {(det.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
                {currentResult.detections.length === 0 && (
                  <p className="text-gray-400 text-center py-4">No detections</p>
                )}
              </div>
            </div>

            {/* Video Stats */}
            {videoResults.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm p-6">
                <h3 className="font-medium text-gray-900 dark:text-white mb-4">
                  Video Summary
                </h3>
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Frames Analyzed</span>
                    <span className="font-medium text-gray-900 dark:text-white">{videoResults.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Avg. People/Frame</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {(videoResults.reduce((sum, r) => sum + r.count, 0) / videoResults.length).toFixed(1)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Max People</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {Math.max(...videoResults.map(r => r.count))}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Min People</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {Math.min(...videoResults.map(r => r.count))}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
