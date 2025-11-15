import type { Route } from "./+types/home";
import { useState } from "react";
import { scribeFile, scribeUrl, LANGUAGE_CODES } from "../lib/api";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Skryba - Multilingual Media Transcription & Summarization" },
    { name: "description", content: "Transcribe, translate, and summarize audio/video in 50+ languages" },
  ];
}

export default function Home() {
  const [mode, setMode] = useState<"file" | "url">("file");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [url, setUrl] = useState("");
  const [language, setLanguage] = useState("en_XX");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let blob: Blob;
      if (mode === "file") {
        if (!selectedFile) {
          throw new Error("Please select a file");
        }
        blob = await scribeFile(selectedFile, language);
      } else {
        if (!url.trim()) {
          throw new Error("Please enter a URL");
        }
        blob = await scribeUrl(url, language);
      }

      // Download the ZIP file
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = `skryba-results-${Date.now()}.zip`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);

      // Reset form
      setSelectedFile(null);
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-4">
              Skryba
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300">
              Multilingual Media Transcription & Summarization
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
              Transcribe, translate, and summarize audio/video in 50+ languages
            </p>
          </div>

          {/* Main Card */}
          <div className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl p-8">
            {/* Mode Tabs */}
            <div className="flex gap-2 mb-8 p-1 bg-gray-100 dark:bg-slate-700 rounded-lg">
              <button
                onClick={() => setMode("file")}
                className={`flex-1 py-3 px-6 rounded-md font-medium transition-all ${
                  mode === "file"
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                📁 Upload File
              </button>
              <button
                onClick={() => setMode("url")}
                className={`flex-1 py-3 px-6 rounded-md font-medium transition-all ${
                  mode === "url"
                    ? "bg-blue-600 text-white shadow-md"
                    : "text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-slate-600"
                }`}
              >
                🔗 From URL
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* File Upload Area */}
              {mode === "file" && (
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  className={`border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                    isDragging
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500"
                  }`}
                >
                  <input
                    type="file"
                    id="file-input"
                    onChange={handleFileChange}
                    accept="audio/*,video/*"
                    className="hidden"
                  />
                  <label
                    htmlFor="file-input"
                    className="cursor-pointer block"
                  >
                    <div className="text-6xl mb-4">🎵</div>
                    {selectedFile ? (
                      <div>
                        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                          {selectedFile.name}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.preventDefault();
                            setSelectedFile(null);
                          }}
                          className="mt-4 text-blue-600 dark:text-blue-400 hover:underline"
                        >
                          Choose different file
                        </button>
                      </div>
                    ) : (
                      <div>
                        <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                          Drop audio or video file here
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          or click to browse
                        </p>
                      </div>
                    )}
                  </label>
                </div>
              )}

              {/* URL Input */}
              {mode === "url" && (
                <div>
                  <label
                    htmlFor="url-input"
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                  >
                    Media URL
                  </label>
                  <input
                    type="url"
                    id="url-input"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="https://example.com/media.mp4"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                  />
                </div>
              )}

              {/* Language Selector */}
              <div>
                <label
                  htmlFor="language"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  Summary Language
                </label>
                <select
                  id="language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-700 dark:text-white"
                >
                  {LANGUAGE_CODES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.label} ({lang.code})
                    </option>
                  ))}
                </select>
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-red-800 dark:text-red-300 text-sm">
                    ⚠️ {error}
                  </p>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading || (mode === "file" && !selectedFile) || (mode === "url" && !url.trim())}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-semibold py-4 px-6 rounded-lg transition-all shadow-lg hover:shadow-xl"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-3">
                    <svg
                      className="animate-spin h-5 w-5"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                      ></circle>
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    Processing...
                  </span>
                ) : (
                  "🚀 Start Transcription"
                )}
              </button>
            </form>
          </div>

          {/* Info Footer */}
          <div className="mt-8 text-center text-sm text-gray-600 dark:text-gray-400">
            <p>
              Results include: transcription (SRT), grouped subtitles, and AI-generated summary
            </p>
            <p className="mt-2">
              Powered by Whisper, MBART-50, and Granite models
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
