export type ApiErrorKind = 'configuration' | 'network' | 'timeout' | 'http' | 'response';

export class ApiError extends Error {
  readonly kind: ApiErrorKind;
  readonly status: number | undefined;
  readonly requestId: string | undefined;

  constructor(
    message: string,
    kind: ApiErrorKind,
    status?: number,
    requestId?: string,
  ) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
    this.requestId = requestId;
  }
}
