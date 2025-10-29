'use client'

import React, { useState } from 'react'
import { Upload, Database, Activity, Settings, Download, Zap, FileText, AlertTriangle, CheckCircle, Loader2 } from 'lucide-react'

interface UploadStatus {
  isUploading: boolean
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

export function AdminUtilities() {
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
    isUploading: false,
    message: '',
    type: 'info'
  })

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>, uploadType: string) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploadStatus({
      isUploading: true,
      message: `Uploading ${uploadType} data...`,
      type: 'info'
    })

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('type', uploadType)

      // Connect to your backend upload endpoint
      const response = await fetch('/api/admin/upload', {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        setUploadStatus({
          isUploading: false,
          message: `${uploadType} data uploaded successfully`,
          type: 'success'
        })
      } else {
        throw new Error(`Upload failed: ${response.statusText}`)
      }
    } catch (error) {
      setUploadStatus({
        isUploading: false,
        message: error instanceof Error ? error.message : 'Upload failed',
        type: 'error'
      })
    }

    // Clear status after 5 seconds
    setTimeout(() => {
      setUploadStatus({ isUploading: false, message: '', type: 'info' })
    }, 5000)
  }

  const triggerDataRefresh = async (dataSource: string) => {
    setUploadStatus({
      isUploading: true,
      message: `Refreshing ${dataSource} data...`,
      type: 'info'
    })

    try {
      const response = await fetch(`/api/admin/refresh/${dataSource}`, {
        method: 'POST',
      })

      if (response.ok) {
        setUploadStatus({
          isUploading: false,
          message: `${dataSource} data refreshed successfully`,
          type: 'success'
        })
      } else {
        throw new Error(`Refresh failed: ${response.statusText}`)
      }
    } catch (error) {
      setUploadStatus({
        isUploading: false,
        message: error instanceof Error ? error.message : 'Refresh failed',
        type: 'error'
      })
    }

    setTimeout(() => {
      setUploadStatus({ isUploading: false, message: '', type: 'info' })
    }, 5000)
  }

  const StatusIcon = () => {
    if (uploadStatus.isUploading) return <Loader2 className="w-4 h-4 animate-spin" />
    switch (uploadStatus.type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-buy-primary" />
      case 'error': return <AlertTriangle className="w-4 h-4 text-sell-critical" />
      case 'warning': return <AlertTriangle className="w-4 h-4 text-sell-caution" />
      default: return <Activity className="w-4 h-4 text-accent-purple" />
    }
  }

  return (
    <div className="space-y-8">
      {/* Status Bar */}
      {uploadStatus.message && (
        <div className={`flex items-center space-x-3 p-4 rounded-lg border ${
          uploadStatus.type === 'success' 
            ? 'bg-buy-primary/10 border-buy-primary/20 text-buy-primary'
            : uploadStatus.type === 'error'
            ? 'bg-sell-critical/10 border-sell-critical/20 text-sell-critical'
            : uploadStatus.type === 'warning'
            ? 'bg-sell-caution/10 border-sell-caution/20 text-sell-caution'
            : 'bg-accent-purple/10 border-accent-purple/20 text-accent-purple'
        }`}>
          <StatusIcon />
          <span className="font-medium">{uploadStatus.message}</span>
        </div>
      )}

      {/* Data Upload Section */}
      <div className="bg-background-secondary rounded-lg border border-border-primary p-6 shadow-depth">
        <div className="flex items-center space-x-3 mb-6">
          <Upload className="w-6 h-6 text-accent-purple" />
          <h2 className="text-xl font-semibold text-text-primary">Data Upload Center</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Price Data Upload */}
          <div className="bg-background-tertiary rounded-lg p-6 border border-border-secondary">
            <div className="flex items-center space-x-2 mb-4">
              <Database className="w-5 h-5 text-buy-primary" />
              <h3 className="font-semibold text-text-primary">Price Data</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Upload soybean oil, corn, crude oil, and palm oil price data
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={(e) => handleFileUpload(e, 'prices')}
              className="hidden"
              id="price-upload"
              disabled={uploadStatus.isUploading}
            />
            <label
              htmlFor="price-upload"
              className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg border border-buy-primary/30 text-buy-primary hover:bg-buy-primary/10 transition-colors cursor-pointer ${
                uploadStatus.isUploading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Upload Prices</span>
            </label>
          </div>

          {/* Weather Data Upload */}
          <div className="bg-background-tertiary rounded-lg p-6 border border-border-secondary">
            <div className="flex items-center space-x-2 mb-4">
              <Activity className="w-5 h-5 text-accent-green" />
              <h3 className="font-semibold text-text-primary">Weather Data</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Upload Brazil, Argentina, and US weather/harvest data
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={(e) => handleFileUpload(e, 'weather')}
              className="hidden"
              id="weather-upload"
              disabled={uploadStatus.isUploading}
            />
            <label
              htmlFor="weather-upload"
              className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg border border-accent-green/30 text-accent-green hover:bg-accent-green/10 transition-colors cursor-pointer ${
                uploadStatus.isUploading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Upload Weather</span>
            </label>
          </div>

          {/* Economic Data Upload */}
          <div className="bg-background-tertiary rounded-lg p-6 border border-border-secondary">
            <div className="flex items-center space-x-2 mb-4">
              <FileText className="w-5 h-5 text-accent-purple" />
              <h3 className="font-semibold text-text-primary">Economic Data</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Upload VIX, currency, and economic indicators
            </p>
            <input
              type="file"
              accept=".csv,.xlsx,.json"
              onChange={(e) => handleFileUpload(e, 'economic')}
              className="hidden"
              id="economic-upload"
              disabled={uploadStatus.isUploading}
            />
            <label
              htmlFor="economic-upload"
              className={`flex items-center justify-center space-x-2 px-4 py-2 rounded-lg border border-accent-purple/30 text-accent-purple hover:bg-accent-purple/10 transition-colors cursor-pointer ${
                uploadStatus.isUploading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Upload className="w-4 h-4" />
              <span>Upload Economic</span>
            </label>
          </div>
        </div>
      </div>

      {/* Data Refresh Section */}
      <div className="bg-background-secondary rounded-lg border border-border-primary p-6 shadow-depth">
        <div className="flex items-center space-x-3 mb-6">
          <Zap className="w-6 h-6 text-buy-accent" />
          <h2 className="text-xl font-semibold text-text-primary">Live Data Refresh</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { name: 'BigQuery Models', key: 'models' },
            { name: 'Market Prices', key: 'prices' },
            { name: 'Weather Data', key: 'weather' },
            { name: 'Social Sentiment', key: 'sentiment' }
          ].map((source) => (
            <button
              key={source.key}
              onClick={() => triggerDataRefresh(source.key)}
              disabled={uploadStatus.isUploading}
              className={`flex items-center justify-center space-x-2 px-4 py-3 rounded-lg border border-buy-accent/30 text-buy-accent hover:bg-buy-accent/10 transition-colors ${
                uploadStatus.isUploading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <Zap className="w-4 h-4" />
              <span>Refresh {source.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* System Utilities */}
      <div className="bg-background-secondary rounded-lg border border-border-primary p-6 shadow-depth">
        <div className="flex items-center space-x-3 mb-6">
          <Settings className="w-6 h-6 text-text-secondary" />
          <h2 className="text-xl font-semibold text-text-primary">System Utilities</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Model Status */}
          <div className="bg-background-tertiary rounded-lg p-4 border border-border-secondary">
            <h3 className="font-semibold text-text-primary mb-2">Vertex AI Models</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">1W Model:</span>
                <span className="text-buy-primary">ACTIVE (1.72% MAPE)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">6M Model:</span>
                <span className="text-buy-primary">ACTIVE (2.15% MAPE)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">3M Model:</span>
                <span className="text-sell-caution">TRAINING</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">1M Model:</span>
                <span className="text-text-tertiary">QUEUED</span>
              </div>
            </div>
          </div>

          {/* Data Health */}
          <div className="bg-background-tertiary rounded-lg p-4 border border-border-secondary">
            <h3 className="font-semibold text-text-primary mb-2">Data Health</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-text-secondary">BigQuery:</span>
                <span className="text-buy-primary">HEALTHY</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">API Endpoints:</span>
                <span className="text-buy-primary">ONLINE</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Dashboard:</span>
                <span className="text-buy-primary">OPERATIONAL</span>
              </div>
              <div className="flex justify-between">
                <span className="text-text-secondary">Last Update:</span>
                <span className="text-text-secondary">2 min ago</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-background-tertiary rounded-lg p-4 border border-border-secondary">
            <h3 className="font-semibold text-text-primary mb-2">Quick Actions</h3>
            <div className="space-y-2">
              <button className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-background-primary rounded transition-colors">
                <Download className="w-4 h-4 inline mr-2" />
                Export Training Data
              </button>
              <button className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-background-primary rounded transition-colors">
                <Activity className="w-4 h-4 inline mr-2" />
                View System Logs
              </button>
              <button className="w-full text-left px-3 py-2 text-sm text-text-secondary hover:bg-background-primary rounded transition-colors">
                <Settings className="w-4 h-4 inline mr-2" />
                Model Configuration
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
