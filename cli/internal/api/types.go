package api

// Task mirrors the task serialisation from the Flask API.
type Task struct {
	ID                       string  `json:"id"`
	ProjectID                string  `json:"project_id"`
	ProjectSectionID         *string `json:"project_section_id"`
	Title                    string  `json:"title"`
	Description              *string `json:"description"`
	Status                   string  `json:"status"`
	Priority                 int     `json:"priority"`
	Phase                    string  `json:"phase"`
	AssigneeType             *string `json:"assignee_type"`
	AssigneeName             *string `json:"assignee_name"`
	EstimatedDurationSeconds *int    `json:"estimated_duration_seconds"`
	ClaimedBy                *string `json:"claimed_by"`
	ClaimedUntil             *string `json:"claimed_until"`
	LeaseVersion             int     `json:"lease_version"`
	ValidationExpectations   *string `json:"validation_expectations"`
	CompletionEvidence       *string `json:"completion_evidence"`
	CreatedAt                string  `json:"created_at"`
	UpdatedAt                string  `json:"updated_at"`
	Version                  int     `json:"version"`
}

// TaskList is the paginated task list response.
type TaskList struct {
	Items   []Task `json:"items"`
	Page    int    `json:"page"`
	PerPage int    `json:"per_page"`
	Total   int    `json:"total"`
	Pages   int    `json:"pages"`
}

// Project mirrors the project serialisation from the Flask API.
type Project struct {
	ID           string  `json:"id"`
	Name         string  `json:"name"`
	Slug         string  `json:"slug"`
	ProjectType  string  `json:"project_type"`
	GitRemoteURL *string `json:"git_remote_url"`
	LocalPath    *string `json:"local_path"`
	Environment  string  `json:"environment"`
	DefaultAgent *string `json:"default_agent"`
	CreatedAt    string  `json:"created_at"`
	UpdatedAt    string  `json:"updated_at"`
	Version      int     `json:"version"`
}

// ProjectList is the paginated project list response.
type ProjectList struct {
	Items   []Project `json:"items"`
	Page    int       `json:"page"`
	PerPage int       `json:"per_page"`
	Total   int       `json:"total"`
	Pages   int       `json:"pages"`
}

// ProjectStatus mirrors the project_status serialisation.
type ProjectStatus struct {
	ID               string  `json:"id"`
	ProjectID        string  `json:"project_id"`
	ProjectSectionID *string `json:"project_section_id"`
	Status           string  `json:"status"`
	Phase            string  `json:"phase"`
	Summary          *string `json:"summary"`
	Reason           *string `json:"reason"`
	CreatedAt        string  `json:"created_at"`
	UpdatedAt        string  `json:"updated_at"`
	Version          int     `json:"version"`
}

// ProjectStatusList is the paginated project status list response.
type ProjectStatusList struct {
	Items   []ProjectStatus `json:"items"`
	Page    int             `json:"page"`
	PerPage int             `json:"per_page"`
	Total   int             `json:"total"`
	Pages   int             `json:"pages"`
}

// APIError is the standard error shape returned by the Flask API.
type APIError struct {
	Error struct {
		Code    string `json:"code"`
		Message string `json:"message"`
	} `json:"error"`
}

// Health is the /health response.
type Health struct {
	Status string `json:"status"`
	Env    string `json:"env"`
	DB     string `json:"db"`
}
