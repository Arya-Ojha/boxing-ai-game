using UnityEngine;
using System.Collections;

public class BoxingCharacter : MonoBehaviour
{
    [Header("Character Settings")]
    public string characterName = "Boxer";
    public int maxHealth = 100;
    public float moveSpeed = 5f;
    public float rotationSpeed = 10f;
    
    [Header("Animation Settings")]
    public Animator animator;
    public float animationBlendTime = 0.1f;
    
    [Header("Move Animations")]
    public string jabAnimation = "Jab";
    public string crossAnimation = "Cross";
    public string hookAnimation = "Hook";
    public string uppercutAnimation = "Uppercut";
    public string blockAnimation = "Block";
    public string dodgeAnimation = "Dodge";
    public string guardAnimation = "Guard";
    public string idleAnimation = "Idle";
    public string hurtAnimation = "Hurt";
    
    [Header("Audio")]
    public AudioSource audioSource;
    public AudioClip jabSound;
    public AudioClip crossSound;
    public AudioClip hookSound;
    public AudioClip uppercutSound;
    public AudioClip blockSound;
    public AudioClip dodgeSound;
    public AudioClip hurtSound;
    
    // Character state
    private int currentHealth;
    private int currentScore;
    private bool isBlocking = false;
    private bool isDodging = false;
    private bool isPerformingMove = false;
    private string lastMove = "";
    
    // Animation parameters
    private readonly int healthParam = Animator.StringToHash("Health");
    private readonly int isBlockingParam = Animator.StringToHash("IsBlocking");
    private readonly int isDodgingParam = Animator.StringToHash("IsDodging");
    private readonly int moveTriggerParam = Animator.StringToHash("MoveTrigger");
    private readonly int moveTypeParam = Animator.StringToHash("MoveType");
    private readonly int confidenceParam = Animator.StringToHash("Confidence");
    
    void Start()
    {
        InitializeCharacter();
    }
    
    void Update()
    {
        UpdateAnimations();
    }
    
    private void InitializeCharacter()
    {
        currentHealth = maxHealth;
        currentScore = 0;
        
        // Get animator if not assigned
        if (animator == null)
            animator = GetComponent<Animator>();
        
        // Get audio source if not assigned
        if (audioSource == null)
            audioSource = GetComponent<AudioSource>();
        
        // Set initial animation state
        if (animator != null)
        {
            animator.SetInteger(healthParam, currentHealth);
            animator.SetBool(isBlockingParam, false);
            animator.SetBool(isDodgingParam, false);
        }
        
        Debug.Log($"Initialized character: {characterName}");
    }
    
    public void PerformMove(string moveType, float confidence)
    {
        if (isPerformingMove)
            return;
        
        lastMove = moveType;
        isPerformingMove = true;
        
        // Set animation parameters
        if (animator != null)
        {
            animator.SetTrigger(moveTriggerParam);
            animator.SetInteger(moveTypeParam, GetMoveTypeHash(moveType));
            animator.SetFloat(confidenceParam, confidence);
        }
        
        // Play sound effect
        PlayMoveSound(moveType);
        
        // Log the move
        Debug.Log($"{characterName} performed {moveType} with confidence {confidence}");
        
        // Reset move state after animation
        StartCoroutine(ResetMoveState());
    }
    
    private int GetMoveTypeHash(string moveType)
    {
        switch (moveType.ToLower())
        {
            case "jab": return 1;
            case "cross": return 2;
            case "hook": return 3;
            case "uppercut": return 4;
            case "block": return 5;
            case "dodge": return 6;
            case "guard": return 7;
            default: return 0;
        }
    }
    
    private void PlayMoveSound(string moveType)
    {
        if (audioSource == null)
            return;
        
        AudioClip clip = null;
        switch (moveType.ToLower())
        {
            case "jab":
                clip = jabSound;
                break;
            case "cross":
                clip = crossSound;
                break;
            case "hook":
                clip = hookSound;
                break;
            case "uppercut":
                clip = uppercutSound;
                break;
            case "block":
                clip = blockSound;
                break;
            case "dodge":
                clip = dodgeSound;
                break;
        }
        
        if (clip != null)
        {
            audioSource.PlayOneShot(clip);
        }
    }
    
    private IEnumerator ResetMoveState()
    {
        // Wait for animation to complete
        yield return new WaitForSeconds(1.0f);
        isPerformingMove = false;
    }
    
    public void SetHealth(int health)
    {
        int oldHealth = currentHealth;
        currentHealth = Mathf.Clamp(health, 0, maxHealth);
        
        // Update animator
        if (animator != null)
        {
            animator.SetInteger(healthParam, currentHealth);
        }
        
        // Play hurt animation if health decreased
        if (currentHealth < oldHealth)
        {
            PlayHurtAnimation();
        }
        
        Debug.Log($"{characterName} health: {oldHealth} -> {currentHealth}");
    }
    
    public void SetScore(int score)
    {
        currentScore = score;
        Debug.Log($"{characterName} score: {currentScore}");
    }
    
    public void SetBlocking(bool blocking)
    {
        isBlocking = blocking;
        
        if (animator != null)
        {
            animator.SetBool(isBlockingParam, blocking);
        }
        
        if (blocking)
        {
            PlayMoveSound("block");
        }
        
        Debug.Log($"{characterName} blocking: {blocking}");
    }
    
    public void SetDodging(bool dodging)
    {
        isDodging = dodging;
        
        if (animator != null)
        {
            animator.SetBool(isDodgingParam, dodging);
        }
        
        if (dodging)
        {
            PlayMoveSound("dodge");
        }
        
        Debug.Log($"{characterName} dodging: {dodging}");
    }
    
    public void SetNeutral()
    {
        SetBlocking(false);
        SetDodging(false);
    }
    
    private void PlayHurtAnimation()
    {
        if (animator != null)
        {
            animator.SetTrigger("Hurt");
        }
        
        if (audioSource != null && hurtSound != null)
        {
            audioSource.PlayOneShot(hurtSound);
        }
    }
    
    private void UpdateAnimations()
    {
        // Update animation blend tree based on health
        if (animator != null)
        {
            float healthPercentage = (float)currentHealth / maxHealth;
            animator.SetFloat("HealthPercentage", healthPercentage);
        }
    }
    
    // Public getters
    public int CurrentHealth => currentHealth;
    public int CurrentScore => currentScore;
    public bool IsBlocking => isBlocking;
    public bool IsDodging => isDodging;
    public bool IsPerformingMove => isPerformingMove;
    public string LastMove => lastMove;
    
    // Animation event handlers (called from animation clips)
    public void OnMoveStart()
    {
        Debug.Log($"{characterName} started move: {lastMove}");
    }
    
    public void OnMoveEnd()
    {
        Debug.Log($"{characterName} finished move: {lastMove}");
    }
    
    public void OnHurtStart()
    {
        Debug.Log($"{characterName} is hurt!");
    }
    
    public void OnHurtEnd()
    {
        Debug.Log($"{characterName} recovered from hurt");
    }
    
    // Visual effects
    public void ShowHitEffect(Vector3 hitPoint)
    {
        // Create hit effect (particles, etc.)
        Debug.Log($"Hit effect at {hitPoint}");
    }
    
    public void ShowBlockEffect()
    {
        // Create block effect
        Debug.Log("Block effect");
    }
    
    public void ShowDodgeEffect()
    {
        // Create dodge effect
        Debug.Log("Dodge effect");
    }
} 