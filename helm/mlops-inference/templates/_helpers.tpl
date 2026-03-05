{{- define "mlops-inference.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "mlops-inference.fullname" -}}
{{- default "mlops-inference" .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "mlops-inference.labels" -}}
app.kubernetes.io/name: {{ include "mlops-inference.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- define "mlops-inference.selectorLabels" -}}
app: mlops-inference
{{- end }}
