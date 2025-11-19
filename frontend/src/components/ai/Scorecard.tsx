import React from 'react';

interface CriteriaScore {
  criterion_name: string;
  score: number;
  explanation: string;
  citations: Array<{
    doc_id: number;
    section?: string;
    relevance_score: number;
    excerpt?: string;
  }>;
}

interface ScorecardProps {
  finalScore: number;
  criteria: CriteriaScore[];
  summary: string;
  improvementTip?: string;
  citations: Array<{
    doc_id: number;
    section?: string;
    relevance_score: number;
    excerpt?: string;
  }>;
}

export const Scorecard: React.FC<ScorecardProps> = ({
  finalScore,
  criteria,
  summary,
  improvementTip,
  citations,
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 8) return 'bg-green-500';
    if (score >= 6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="space-y-6">
      {/* Overall Score */}
      <div className="bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg p-6 text-white">
        <div className="text-sm font-medium opacity-90 mb-2">Overall Score</div>
        <div className="text-4xl font-bold">{finalScore.toFixed(1)} / 10.0</div>
      </div>

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h3 className="font-semibold text-gray-900 mb-2">Summary</h3>
        <p className="text-gray-700 text-sm">{summary}</p>
      </div>

      {/* Criteria Breakdown */}
      <div className="space-y-4">
        <h3 className="font-semibold text-gray-900">Criteria Breakdown</h3>
        {criteria.map((criterion, index) => (
          <div key={index} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900">{criterion.criterion_name}</h4>
              <span className="text-lg font-semibold text-gray-700">
                {criterion.score.toFixed(1)}
              </span>
            </div>
            
            {/* Score bar */}
            <div className="w-full h-2 bg-gray-200 rounded-full mb-3 overflow-hidden">
              <div
                className={`h-full ${getScoreColor(criterion.score)} transition-all`}
                style={{ width: `${(criterion.score / 10) * 100}%` }}
              />
            </div>

            <p className="text-sm text-gray-600 mb-2">{criterion.explanation}</p>

            {criterion.citations.length > 0 && (
              <div className="mt-2 text-xs text-gray-500">
                <span className="font-medium">Citations:</span>{' '}
                {criterion.citations.map((cit, i) => (
                  <span key={i}>
                    Doc #{cit.doc_id}
                    {cit.section && ` (${cit.section})`}
                    {i < criterion.citations.length - 1 && ', '}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Improvement Tip */}
      {improvementTip && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">💡 Improvement Tip</h3>
          <p className="text-blue-800 text-sm">{improvementTip}</p>
        </div>
      )}

      {/* All Citations */}
      {citations.length > 0 && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h3 className="font-semibold text-gray-900 mb-2">All Citations</h3>
          <div className="space-y-2 text-sm">
            {citations.map((citation, index) => (
              <div key={index} className="text-gray-700">
                <span className="font-medium">Doc #{citation.doc_id}</span>
                {citation.section && <span> - {citation.section}</span>}
                {citation.excerpt && (
                  <div className="text-xs text-gray-600 italic mt-1 ml-4">
                    "{citation.excerpt}"
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

