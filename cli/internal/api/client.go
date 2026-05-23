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
	path := "/api/projects/" + projectID + "/tasks?" + params.Encode()
	data, _, err := c.do("GET", path, nil)
	if err != nil {
		return TaskList{}, err
	}
	return decode[TaskList](data)
}

// TaskListOpts holds optional filters for ListTasks.
type TaskListOpts struct {
	Page    int
	PerPage int
	Status  string
	Phase   string
}

func (c *Client) GetTask(taskID string) (Task, error) {
	data, _, err := c.do("GET", "/api/tasks/"+taskID, nil)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) ClaimTask(taskID, agentName string, durationSeconds int) (Task, error) {
	body := map[string]any{"agent_name": agentName}
	if durationSeconds > 0 {
		body["duration_seconds"] = durationSeconds
	}
	data, _, err := c.do("POST", "/api/tasks/"+taskID+"/claim", body)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) HeartbeatTask(taskID, agentName string) (Task, error) {
	body := map[string]any{"agent_name": agentName}
	data, _, err := c.do("POST", "/api/tasks/"+taskID+"/heartbeat", body)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) CompleteTask(taskID, agentName, evidence string) (Task, error) {
	body := map[string]any{
		"agent_name": agentName,
		"evidence":   evidence,
	}
	data, _, err := c.do("POST", "/api/tasks/"+taskID+"/complete", body)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

func (c *Client) BlockTask(taskID, agentName, reason string) (Task, error) {
	body := map[string]any{
		"agent_name": agentName,
		"reason":     reason,
	}
	data, _, err := c.do("POST", "/api/tasks/"+taskID+"/block", body)
	if err != nil {
		return Task{}, err
	}
	return decode[Task](data)
}

// ── project status ────────────────────────────────────────────────────────────

func (c *Client) ListProjectStatus(projectID string) (ProjectStatusList, error) {
	data, _, err := c.do("GET", "/api/projects/"+projectID+"/status", nil)
	if err != nil {
		return ProjectStatusList{}, err
	}
	return decode[ProjectStatusList](data)
}
