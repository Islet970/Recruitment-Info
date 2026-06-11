export interface User {
  id: number;
  username: string;
  email: string;
  avatar_url: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface CompanyBrief {
  id: number;
  name: string;
  short_name: string | null;
  scale: string | null;
  financing_stage: string | null;
  industry: string | null;
  address: string | null;
  logo_url: string | null;
  website: string | null;
  description: string | null;
  benefits: string | null;
  position_count: number;
}

export interface PositionBriefForCompany {
  id: number;
  name: string;
  recruit_type: string;
  city: string | null;
  location: string | null;
  salary_text: string | null;
  salary_type: string | null;
  salary_min: number;
  salary_max: number;
  education_required: string | null;
  experience_required: string | null;
  tags: string | null;
  publish_time: string | null;
}

export interface CompanyDetail extends CompanyBrief {
  positions: PositionBriefForCompany[];
}

export interface PositionBrief {
  id: number;
  name: string;
  recruit_type: string;
  city: string | null;
  location: string | null;
  salary_text: string | null;
  salary_type: string | null;
  salary_min: number;
  salary_max: number;
  education_required: string | null;
  experience_required: string | null;
  tags: string | null;
  publish_time: string | null;
  company: CompanyBrief | null;
  category_name: string | null;
}

export interface PositionDetail extends PositionBrief {
  url: string | null;
  responsibility: string | null;
  requirement: string | null;
  bonus: string | null;
  source: string | null;
  skills: string[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DashboardSummary {
  total_positions: number;
  total_companies: number;
  total_skills: number;
}

export interface TrendPoint { date: string; count: number; }
export interface CategoryDistribution { name: string; value: number; }
export interface ScaleDistribution { scale: string; count: number; }
export interface EducationDistribution { education: string; count: number; }
export interface SkillCount { name: string; count: number; }
export interface SalaryBucket { range: string; count: number; }

export interface BoxPlotData {
  name: string; min: number; q1: number; median: number; q3: number; max: number; mean: number;
}

export interface IndustryDistribution { name: string; value: number; }
export interface CompanyPositionCount { name: string; count: number; }
export interface FinancingStage { stage: string; count: number; }
export interface CityDistribution { city: string; count: number; }

export interface Resume {
  id: number;
  file_name: string;
  file_type: string | null;
  upload_time: string;
}

export interface ResumeAnalysis {
  id: number;
  resume_id: number;
  status: string;
  analysis_result: {
    summary: string;
    strengths: string[];
    weaknesses: string[];
    detailed_analysis: string;
  } | null;
  extracted_skills: string[];
  experience_years: number | null;
  education_level: string | null;
  recommended_directions: string[];
  created_at: string | null;
  updated_at: string | null;
}

export interface RecommendedPosition {
  position: PositionBrief;
  match_score: number;
  match_reasons: string[];
}
