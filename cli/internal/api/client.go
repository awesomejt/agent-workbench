package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

// Client is an HTTP client for the Agent Workbench API.
type Client struct {
	BaseURL    string
	httpClient *http.Client
}

// New returns a Client pointed at baseURL.
func New(baseURL string) *Client {
	return &Client{
		BaseURL: strings.TrimRight(baseURL, "/"),
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ── helpers ──────────────────────────────────────────────────────────────────

func (c *Client) url(path string) string {
	return c.BaseURL + path
}

func (c *Client) do(method, path string, body any) ([]byte, int, error) {
	return c.doWithHeaders(method, path, body, nil)
}

func (c *Client) doWithHeaders(method, path string, body any, headers map[string]string) ([]byte, int, error) {
	var reqBody io.Reader
	if body != nil {
		b, err := json.Marshal(body)
		if err != nil {
			return nil, 0, fmt.Errorf("marshal request: %w", err)
		}
		reqBody = bytes.NewReader(b)
	}

	req, err := http.NewRequest(method, c.url(path), reqBody)
	if err != nil {
		return nil, 0, fmt.Errorf("build request: %w", err)
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Accept", "application/json")
	for k, v := range headers {
		req.Header.Set(k, v)
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, 0, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	data, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, resp.StatusCode, fmt.Errorf("read response: %w", err)
	}

	if resp.StatusCode >= 400 {
		var apiErr APIError
		if jsonErr := json.Unmarshal(data, &apiErr); jsonErr == nil && apiErr.Error.Message != "" {
			return nil, resp.StatusCode, fmt.Errorf("API %d: %s", resp.StatusCode, apiErr.Error.Message)
		}
		return nil, resp.StatusCode, fmt.Errorf("API %d: %s", resp.StatusCode, string(data))
	}

	return data, resp.StatusCode, nil
}

func decode[T any](data []byte) (T, error) {
	var v T
	if err := json.Unmarshal(data, &v); err != nil {
		return v, fmt.Errorf("decode response: %w", err)
	}
	return v, nil
}

// ── health ───────────────────────────────────────────────────────────────────

func (c *Client) Health() (Health, error) {
	data, _, err := c.do("GET", "/health", nil)
	if err != nil {
		return Health{}, err
	}
	return decode[Health](data)
}

// ── projects ─────────────────────────────────────────────────────────────────

func (c *Client) ListProjects(page, perPage int) (ProjectList, error) {
	path := fmt.Sprintf("/api/projects?page=%d&per_page=%d", page, perPage)
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return ProjectList{}, err
	}
	return decode[ProjectList](data)
}

// ProjectBySlug fetches the first project matching slug.
func (c *Client) ProjectBySlug(slug string) (Project, error) {
	list, err := c.ListProjects(1, 100)
	if err != nil {
		return Project{}, err
	}
	for _, p := range list.Items {
		if p.Slug == slug {
			return p, nil
		}
	}
	return Project{}, fmt.Errorf("project %q not found", slug)
}

// ── tasks ─────────────────────────────────────────────────────────────────────

func (c *Client) ListTasks(projectID string, opts TaskListOpts) (TaskList, error) {
	params := url.Values{}
	params.Set("page", strconv.Itoa(opts.Page))
	params.Set("per_page", strconv.Itoa(opts.PerPage))
	if opts.Status != "" {
		params.Set("status", opts.Status)
	}
	if opts.Phase != "" {
		params.Set("phase", opts.Phase)
	}
	if opts.Available {
		params.Set("available", "true")
	}
	path := "/api/projects/" + projectID + "/tasks?" + params.Encode()
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return TaskList{}, err
	}
	return decode[TaskList](data)
}

// TaskListOpts holds optional filters for ListTasks.
type TaskListOpts struct {
	Page      int
	PerPage   int
	Status    string
	Phase     string
	Available bool // true = pending tasks with no active lease only
}

// CreateTask creates a new task under the given project.
func (c *Client) CreateTask(projectID string, body map[string]any) (Task, error) {
	data, _, err := c.do("POST", "/api/projects/"+projectID+"/tasks", body)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) GetTask(taskID string) (Task, error) {
	data, _, err := c.do("GET", "/api/tasks/"+taskID, nil)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) ClaimTask(taskID, agentName, idempotencyKey string, durationSeconds int) (Task, error) {
	body := map[string]any{"agent_name": agentName}
	if durationSeconds > 0 {
		body["duration_seconds"] = durationSeconds
	}
	headers := idempotencyHeader(idempotencyKey)
	data, _, err := c.doWithHeaders("POST", "/api/tasks/"+taskID+"/claim", body, headers)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) HeartbeatTask(taskID, agentName, idempotencyKey string) (Task, error) {
	body := map[string]any{"agent_name": agentName}
	headers := idempotencyHeader(idempotencyKey)
	data, _, err := c.doWithHeaders("POST", "/api/tasks/"+taskID+"/heartbeat", body, headers)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) CompleteTask(taskID, agentName, evidence, idempotencyKey string) (Task, error) {
	body := map[string]any{
		"agent_name": agentName,
		"evidence":   evidence,
	}
	headers := idempotencyHeader(idempotencyKey)
	data, _, err := c.doWithHeaders("POST", "/api/tasks/"+taskID+"/complete", body, headers)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) BlockTask(taskID, agentName, reason, idempotencyKey string) (Task, error) {
	body := map[string]any{
		"agent_name": agentName,
		"reason":     reason,
	}
	headers := idempotencyHeader(idempotencyKey)
	data, _, err := c.doWithHeaders("POST", "/api/tasks/"+taskID+"/block", body, headers)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

// idempotencyHeader returns a header map with Idempotency-Key set if key is non-empty.
func idempotencyHeader(key string) map[string]string {
	if key == "" {
		return nil
	}
	return map[string]string{"Idempotency-Key": key}
}

// GetProject fetches a single project by ID.
func (c *Client) GetProject(projectID string) (Project, error) {
	data, _, err := c.do("GET", "/api/projects/"+projectID, nil)
	if err != nil {
		return Project{}, err
	}
	return decode[Project](data)
}

// CreateProject creates a new project.
func (c *Client) CreateProject(body map[string]any) (Project, error) {
	data, _, err := c.do("POST", "/api/projects", body)
	if err != nil {
		return Project{}, err
	}
	return decode[Project](data)
}

// UpdateProject patches a project by ID.
func (c *Client) UpdateProject(projectID string, body map[string]any) (Project, error) {
	data, _, err := c.do("PATCH", "/api/projects/"+projectID, body)
	if err != nil {
		return Project{}, err
	}
	return decode[Project](data)
}

// ── project status ────────────────────────────────────────────────────────────

func (c *Client) ListProjectStatus(projectID string) (ProjectStatusList, error) {
	data, _, err := c.do("GET", "/api/projects/"+projectID+"/status", nil)
	if err != nil {
		return ProjectStatusList{}, err
	}
	return decode[ProjectStatusList](data)
}

// CreateStatus creates a new status record for a project.
func (c *Client) CreateStatus(projectID string, body map[string]any) (ProjectStatus, error) {
	data, _, err := c.do("POST", "/api/projects/"+projectID+"/status", body)
	if err != nil {
		return ProjectStatus{}, err
	}
	return decode[ProjectStatus](data)
}

// UpdateStatus patches a project status record.
func (c *Client) UpdateStatus(projectID, statusID string, body map[string]any) (ProjectStatus, error) {
	path := "/api/projects/" + projectID + "/status/" + statusID
	data, _, err := c.do("PATCH", path, body)
	if err != nil {
		return ProjectStatus{}, err
	}
	return decode[ProjectStatus](data)
}

// ── sections ──────────────────────────────────────────────────────────────────

func (c *Client) ListSections(projectID string) (SectionList, error) {
	data, _, err := c.do("GET", "/api/projects/"+projectID+"/sections", nil)
	if err != nil {
		return SectionList{}, err
	}
	return decode[SectionList](data)
}

func (c *Client) CreateSection(projectID string, body map[string]any) (Section, error) {
	data, _, err := c.do("POST", "/api/projects/"+projectID+"/sections", body)
	if err != nil {
		return Section{}, err
	}
	return decode[Section](data)
}

func (c *Client) GetSection(projectID, sectionID string) (Section, error) {
	path := "/api/projects/" + projectID + "/sections/" + sectionID
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return Section{}, err
	}
	return decode[Section](data)
}

func (c *Client) UpdateSection(projectID, sectionID string, body map[string]any) (Section, error) {
	path := "/api/projects/" + projectID + "/sections/" + sectionID
	data, _, err := c.do("PATCH", path, body)
	if err != nil {
		return Section{}, err
	}
	return decode[Section](data)
}

// ── agents ────────────────────────────────────────────────────────────────────

func (c *Client) ListAgents(page, perPage int) (AgentList, error) {
	path := fmt.Sprintf("/api/agents?page=%d&per_page=%d", page, perPage)
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return AgentList{}, err
	}
	return decode[AgentList](data)
}

func (c *Client) CreateAgent(body map[string]any) (Agent, error) {
	data, _, err := c.do("POST", "/api/agents", body)
	if err != nil {
		return Agent{}, err
	}
	return decode[Agent](data)
}

func (c *Client) GetAgent(agentID string) (Agent, error) {
	data, _, err := c.do("GET", "/api/agents/"+agentID, nil)
	if err != nil {
		return Agent{}, err
	}
	return decode[Agent](data)
}

func (c *Client) UpdateAgent(agentID string, body map[string]any) (Agent, error) {
	data, _, err := c.do("PATCH", "/api/agents/"+agentID, body)
	if err != nil {
		return Agent{}, err
	}
	return decode[Agent](data)
}

// ── runs ──────────────────────────────────────────────────────────────────────

// RunMetrics holds optional runtime metrics for a run.
type RunMetrics struct {
	ModelID          string
	PromptTokens     int
	CompletionTokens int
	LatencyMs        int
	PromptCategory   string
}

func applyMetrics(body map[string]any, m RunMetrics) {
	if m.ModelID != "" {
		body["model_id"] = m.ModelID
	}
	if m.PromptTokens > 0 {
		body["prompt_tokens"] = m.PromptTokens
	}
	if m.CompletionTokens > 0 {
		body["completion_tokens"] = m.CompletionTokens
	}
	if m.LatencyMs > 0 {
		body["latency_ms"] = m.LatencyMs
	}
	if m.PromptCategory != "" {
		body["prompt_category"] = m.PromptCategory
	}
}

// CreateRun starts a new run. projectID and agentName are required; taskID may be empty.
func (c *Client) CreateRun(projectID, agentName, taskID, summary string, metrics RunMetrics) (Run, error) {
	body := map[string]any{
		"project_id": projectID,
		"agent_name": agentName,
	}
	if taskID != "" {
		body["task_id"] = taskID
	}
	if summary != "" {
		body["summary"] = summary
	}
	applyMetrics(body, metrics)
	data, _, err := c.do("POST", "/api/runs", body)
	if err != nil {
		return Run{}, err
	}
	return decode[Run](data)
}

func (c *Client) GetRun(runID string) (Run, error) {
	data, _, err := c.do("GET", "/api/runs/"+runID, nil)
	if err != nil {
		return Run{}, err
	}
	return decode[Run](data)
}

func (c *Client) HeartbeatRun(runID string) (Run, error) {
	data, _, err := c.do("POST", "/api/runs/"+runID+"/heartbeat", nil)
	if err != nil {
		return Run{}, err
	}
	return decode[Run](data)
}

func (c *Client) CompleteRun(runID, summary, validationResult string, metrics RunMetrics) (Run, error) {
	body := map[string]any{}
	if summary != "" {
		body["summary"] = summary
	}
	if validationResult != "" {
		body["validation_result"] = validationResult
	}
	applyMetrics(body, metrics)
	data, _, err := c.do("POST", "/api/runs/"+runID+"/complete", body)
	if err != nil {
		return Run{}, err
	}
	return decode[Run](data)
}

func (c *Client) FailRun(runID, summary string, metrics RunMetrics) (Run, error) {
	body := map[string]any{}
	if summary != "" {
		body["summary"] = summary
	}
	applyMetrics(body, metrics)
	data, _, err := c.do("POST", "/api/runs/"+runID+"/fail", body)
	if err != nil {
		return Run{}, err
	}
	return decode[Run](data)
}

// ── events ────────────────────────────────────────────────────────────────────

func (c *Client) ListEvents(projectID string, page, perPage int) (EventList, error) {
	path := fmt.Sprintf("/api/projects/%s/events?page=%d&per_page=%d", projectID, page, perPage)
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return EventList{}, err
	}
	return decode[EventList](data)
}

// AppendEvent posts a new event. body must include event_type; project_id/task_id/run_id are optional.
func (c *Client) AppendEvent(body map[string]any) (Event, error) {
	data, _, err := c.do("POST", "/api/events", body)
	if err != nil {
		return Event{}, err
	}
	return decode[Event](data)
}
