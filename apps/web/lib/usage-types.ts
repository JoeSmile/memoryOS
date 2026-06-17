export type MyUsageRead = {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  quota_enabled: boolean;
  daily_quota: number | null;
};
