package com.resume.builder.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class GeminiService {

    @Value("${gemini.api.key:}")
    private String apiKey;

    private final RestClient restClient;

    public GeminiService() {
        this.restClient = RestClient.builder().build();
    }

    private String getGeminiUrl() {
        return "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=" + apiKey;
    }

    public boolean isApiKeyConfigured() {
        return apiKey != null && !apiKey.trim().isEmpty();
    }

    /**
     * Common method to call the Gemini API
     */
    private String callGemini(String systemInstruction, String userPrompt, Map<String, Object> responseSchema) {
        if (!isApiKeyConfigured()) {
            throw new IllegalStateException("Google Gemini API Key is not configured. Please add it to application.properties or set GEMINI_API_KEY environment variable.");
        }

        // Prepare the request payload
        Map<String, Object> textPart = new HashMap<>();
        textPart.put("text", userPrompt);

        Map<String, Object> contentObj = new HashMap<>();
        contentObj.put("parts", List.of(textPart));

        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("contents", List.of(contentObj));

        // System instruction
        if (systemInstruction != null && !systemInstruction.trim().isEmpty()) {
            Map<String, Object> sysTextPart = new HashMap<>();
            sysTextPart.put("text", systemInstruction);
            Map<String, Object> sysContent = new HashMap<>();
            sysContent.put("parts", List.of(sysTextPart));
            requestBody.put("systemInstruction", sysContent);
        }

        // Generation Config for JSON structured output
        Map<String, Object> generationConfig = new HashMap<>();
        generationConfig.put("responseMimeType", "application/json");
        if (responseSchema != null) {
            generationConfig.put("responseSchema", responseSchema);
        }
        requestBody.put("generationConfig", generationConfig);

        try {
            Map<?, ?> response = restClient.post()
                    .uri(getGeminiUrl())
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(requestBody)
                    .retrieve()
                    .body(Map.class);

            if (response == null) {
                throw new RuntimeException("Empty response from Gemini API");
            }

            // Navigate response: candidates[0].content.parts[0].text
            List<?> candidates = (List<?>) response.get("candidates");
            if (candidates == null || candidates.isEmpty()) {
                throw new RuntimeException("No candidates returned from Gemini API");
            }
            Map<?, ?> candidate = (Map<?, ?>) candidates.get(0);
            Map<?, ?> content = (Map<?, ?>) candidate.get("content");
            List<?> parts = (List<?>) content.get("parts");
            Map<?, ?> part = (Map<?, ?>) parts.get(0);
            return (String) part.get("text");

        } catch (Exception e) {
            throw new RuntimeException("Failed to invoke Gemini API: " + e.getMessage(), e);
        }
    }

    /**
     * Feature 1 & 2: ATS Score & Compatibility Check
     */
    public String analyzeAts(String resumeText) {
        if (!isApiKeyConfigured()) {
            return getLocalAtsHeuristics(resumeText);
        }

        String systemInstruction = "You are an advanced Application Tracking System (ATS) simulator and professional resume reviewer. " +
                "Analyze the formatting, keyword usage, readability, action verbs, and experience quality. " +
                "Determine an ATS score out of 100 and list strengths, weaknesses, and suggestions.";

        String userPrompt = "Analyze this resume text:\n\n" + resumeText;

        // Structured JSON output schema
        Map<String, Object> schema = Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "score", Map.of("type", "INTEGER"),
                        "strengths", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "weaknesses", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "suggestions", Map.of("type", "ARRAY", "items", Map.of("type", "STRING"))
                ),
                "required", List.of("score", "strengths", "weaknesses", "suggestions")
        );

        return callGemini(systemInstruction, userPrompt, schema);
    }

    /**
     * Feature 3: Job Description Matching
     */
    public String matchJobDescription(String resumeText, String jdText) {
        if (!isApiKeyConfigured()) {
            return getLocalJdMatchingMock(resumeText, jdText);
        }

        String systemInstruction = "You are an expert recruiter. Compare the Resume and Job Description. " +
                "Calculate a match percentage, extract matching skills, missing technical skills, missing soft skills, " +
                "recommended keywords, certifications, specific projects to bridge gaps, and a short learning roadmap.";

        String userPrompt = "Resume:\n" + resumeText + "\n\nJob Description:\n" + jdText;

        Map<String, Object> schema = Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "match_percentage", Map.of("type", "INTEGER"),
                        "matching_skills", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "missing_technical_skills", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "missing_soft_skills", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "recommended_keywords", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "recommended_certifications", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "recommended_projects", Map.of("type", "ARRAY", "items", Map.of("type", "STRING")),
                        "learning_roadmap", Map.of("type", "ARRAY", "items", Map.of("type", "STRING"))
                ),
                "required", List.of("match_percentage", "matching_skills", "missing_technical_skills", "missing_soft_skills", "recommended_keywords", "recommended_certifications", "recommended_projects", "learning_roadmap")
        );

        return callGemini(systemInstruction, userPrompt, schema);
    }

    /**
     * Feature 4: Cover Letter Generation
     */
    public String generateCoverLetter(String resumeText, String jdText) {
        if (!isApiKeyConfigured()) {
            return getLocalCoverLetterMock();
        }

        String systemInstruction = "You are an expert career coach. Generate a compelling, tailored cover letter based on the candidate's resume and target job description.";
        String userPrompt = "Resume:\n" + resumeText + "\n\nJob Description:\n" + jdText;

        Map<String, Object> schema = Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "subject", Map.of("type", "STRING"),
                        "salutation", Map.of("type", "STRING"),
                        "body", Map.of("type", "STRING"),
                        "closing", Map.of("type", "STRING"),
                        "full_letter", Map.of("type", "STRING")
                ),
                "required", List.of("subject", "salutation", "body", "closing", "full_letter")
        );

        return callGemini(systemInstruction, userPrompt, schema);
    }

    /**
     * Feature 5: Interview Prep Question Generation
     */
    public String generateInterviewPrep(String resumeText) {
        if (!isApiKeyConfigured()) {
            return getLocalInterviewPrepMock();
        }

        String systemInstruction = "You are an experienced hiring manager. Generate 5 targeted interview questions (with sample answers and rationale) based on the achievements and technical stacks outlined in this resume.";
        String userPrompt = "Resume:\n" + resumeText;

        Map<String, Object> schema = Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "questions", Map.of(
                                "type", "ARRAY",
                                "items", Map.of(
                                        "type", "OBJECT",
                                        "properties", Map.of(
                                                "question", Map.of("type", "STRING"),
                                                "suggested_answer", Map.of("type", "STRING"),
                                                "rationale", Map.of("type", "STRING")
                                        ),
                                        "required", List.of("question", "suggested_answer", "rationale")
                                )
                        )
                ),
                "required", List.of("questions")
        );

        return callGemini(systemInstruction, userPrompt, schema);
    }

    /**
     * Feature 6: Resume Rewriting & Suggestions
     */
    public String generateRewrites(String resumeText) {
        if (!isApiKeyConfigured()) {
            return getLocalRewritesMock();
        }

        String systemInstruction = "You are an expert resume writer. Generate rewritten versions of key bullets and sections in the resume to maximize ATS friendliness, improve verbs, and quantify impact.";
        String userPrompt = "Resume:\n" + resumeText;

        Map<String, Object> schema = Map.of(
                "type", "OBJECT",
                "properties", Map.of(
                        "rewritten_text", Map.of("type", "STRING"),
                        "suggestions", Map.of(
                                "type", "ARRAY",
                                "items", Map.of(
                                        "type", "OBJECT",
                                        "properties", Map.of(
                                                "section", Map.of("type", "STRING"),
                                                "original", Map.of("type", "STRING"),
                                                "improved", Map.of("type", "STRING"),
                                                "reason", Map.of("type", "STRING")
                                        ),
                                        "required", List.of("section", "original", "improved", "reason")
                                )
                        )
                ),
                "required", List.of("rewritten_text", "suggestions")
        );

        return callGemini(systemInstruction, userPrompt, schema);
    }

    // --- FALLBACK LOCAL HEURISTICS / MOCKS ---

    private String getLocalAtsHeuristics(String resumeText) {
        int score = 55;
        if (resumeText.toLowerCase().contains("email") || resumeText.contains("@")) score += 15;
        if (resumeText.toLowerCase().contains("education")) score += 10;
        if (resumeText.toLowerCase().contains("experience")) score += 10;
        if (resumeText.toLowerCase().contains("skills")) score += 10;
        score = Math.min(100, score);

        return "{" +
                "\"score\": " + score + "," +
                "\"strengths\": [\"Resume possesses clear structure with identified headers\", \"Contact email address is present\"]," +
                "\"weaknesses\": [\"Passive verbs are used heavily instead of achievement metrics\", \"Missing target keywords\"]," +
                "\"suggestions\": [\"Replace passive descriptions with action verbs like 'Spearheaded' and 'Optimized'\", \"Configure GEMINI_API_KEY to unlock advanced AI-powered diagnostics\"]" +
                "}";
    }

    private String getLocalJdMatchingMock(String resumeText, String jdText) {
        return "{" +
                "\"match_percentage\": 68," +
                "\"matching_skills\": [\"Java\", \"REST APIs\", \"SQL\"]," +
                "\"missing_technical_skills\": [\"Spring Boot\", \"Docker\", \"AWS\"]," +
                "\"missing_soft_skills\": [\"Agile Leadership\", \"Cross-functional Collaboration\"]," +
                "\"recommended_keywords\": [\"Microservices\", \"CI/CD\", \"Kubernetes\"]," +
                "\"recommended_certifications\": [\"AWS Certified Developer\", \"Oracle Java SE 17 Developer\"]," +
                "\"recommended_projects\": [\"Build a REST API backend deployed using Docker on AWS ECS\", \"Set up a Spring Boot application with a GitHub Actions CI/CD pipeline\"]," +
                "\"learning_roadmap\": [\"Step 1: Complete a Spring Boot fundamentals course (2 weeks)\", \"Step 2: Learn Docker containerization basics (1 week)\", \"Step 3: Deploy your projects to AWS Free Tier (1 week)\"]" +
                "}";
    }

    private String getLocalCoverLetterMock() {
        return "{" +
                "\"subject\": \"Application for Software Engineer Position\"," +
                "\"salutation\": \"Dear Hiring Manager,\"," +
                "\"body\": \"I am writing to express my strong interest in the Software Engineer position. With my solid background in Java development, designing REST APIs, and database engineering, I am confident in my ability to contribute value to your development team immediately. I have a proven track record of constructing robust backend solutions and optimizing query performances.\"," +
                "\"closing\": \"Thank you for your time and consideration. I look forward to the possibility of discussing how my skills align with your team's goals.\"," +
                "\"full_letter\": \"Subject: Application for Software Engineer Position\\n\\nDear Hiring Manager,\\n\\nI am writing to express my strong interest in the Software Engineer position. With my solid background in Java development, designing REST APIs, and database engineering, I am confident in my ability to contribute value to your development team immediately. I have a proven track record of constructing robust backend solutions and optimizing query performances.\\n\\nThank you for your time and consideration. I look forward to the possibility of discussing how my skills align with your team's goals.\\n\\nSincerely,\\n[Your Name]\"" +
                "}";
    }

    private String getLocalInterviewPrepMock() {
        return "{" +
                "\"questions\": [" +
                "  {" +
                "    \"question\": \"Can you describe a challenging backend issue you solved? \"," +
                "    \"suggested_answer\": \"I encountered a slow SQL query in our database. I analyzed the execution plan, found a missing composite index, and added it, which reduced execution time by 80%.\"," +
                "    \"rationale\": \"Shows technical diagnostics skill, understanding of databases, and quantifiable results.\"" +
                "  }," +
                "  {" +
                "    \"question\": \"How do you ensure the security and performance of your REST APIs? \"," +
                "    \"suggested_answer\": \"I implement standard JWT authentication, rate limiting, and input validation, and use caching for read-heavy operations.\"," +
                "    \"rationale\": \"Demonstrates security-first design and performance optimization awareness.\"" +
                "  }" +
                "]" +
                "}";
    }

    private String getLocalRewritesMock() {
        return "{" +
                "\"rewritten_text\": \"# Professional Experience\\n\\n* Spearheaded the migration of legacy APIs to Spring Boot, boosting throughput by 35%\\n* Engineered database indexing strategies that reduced query latency by 50%\", " +
                "\"suggestions\": [" +
                "  {" +
                "    \"section\": \"Experience\"," +
                "    \"original\": \"Worked on writing APIs in Spring Boot\"," +
                "    \"improved\": \"Spearheaded the migration of legacy APIs to Spring Boot, boosting throughput by 35%\"," +
                "    \"reason\": \"Uses a strong action verb and adds a quantifiable metric.\"" +
                "  }," +
                "  {" +
                "    \"section\": \"Experience\"," +
                "    \"original\": \"Helped with database query latency\"," +
                "    \"improved\": \"Engineered database indexing strategies that reduced query latency by 50%\"," +
                "    \"reason\": \"Increases technical depth and measures accomplishment.\"" +
                "  }" +
                "]" +
                "}";
    }
}
