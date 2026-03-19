"""
Client Claude pour l'API Anthropic avec support du streaming.
"""
import asyncio
import logging
from typing import Optional, Callable
from django.conf import settings
import anthropic

logger = logging.getLogger(__name__)


class PlanGenerationError(Exception):
    """Exception levée lors d'erreurs de génération."""
    pass


class ClaudeClient:
    """
    Client pour l'API Claude avec streaming et gestion d'erreurs.
    """
    
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.timeout = settings.AI_TIMEOUT_SECONDS
    
    def call_claude_streaming(
        self,
        prompt: str,
        system_prompt: str,
        job_id: str,
        on_chunk: Optional[Callable[[str, str], None]] = None,
    ) -> str:
        """
        Appelle l'API Claude avec streaming et retourne la réponse complète.

        Paramètres :
        - prompt    : prompt utilisateur (construit par build_landscape_prompt)
        - system_prompt : prompt système
        - job_id    : identifiant du job pour le WebSocket
        - on_chunk  : callback appelé à chaque chunk de texte reçu
                      signature : on_chunk(text: str, accumulated: str)

        Configuration :
        - model      : AI_MODEL (claude-3-5-sonnet-20241022)
        - max_tokens : AI_MAX_TOKENS (4096)
        - timeout    : AI_TIMEOUT_SECONDS (120)

        Gestion d'erreurs :
        - anthropic.APIConnectionError → retry avec backoff exponentiel
        - anthropic.RateLimitError     → attendre 60s puis retry
        - anthropic.APIStatusError 529 → surcharge serveur, retry après 30s
        - Timeout                      → lever PlanGenerationError("timeout")

        Retourne le texte complet accumulé.
        """
        retry_count = 0
        max_retries = settings.AI_MAX_RETRIES
        
        while retry_count <= max_retries:
            try:
                return self._stream_claude_response(
                    prompt, system_prompt, on_chunk
                )
                
            except anthropic.APIConnectionError as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Connexion Claude échec après {max_retries} tentatives: {e}")
                    raise PlanGenerationError(f"Erreur de connexion Claude après {max_retries} tentatives")
                
                # Backoff exponentiel
                wait_time = 2 ** retry_count
                logger.warning(f"Connexion Claude échouée, retry {retry_count}/{max_retries} dans {wait_time}s")
                asyncio.sleep(wait_time)
                
            except anthropic.RateLimitError as e:
                retry_count += 1
                if retry_count > max_retries:
                    logger.error(f"Rate limit Claude dépassé après {max_retries} tentatives: {e}")
                    raise PlanGenerationError("Limite de requêtes Claude dépassée")
                
                logger.warning(f"Rate limit Claude atteint, retry {retry_count}/{max_retries} dans 60s")
                asyncio.sleep(60)
                
            except anthropic.APIStatusError as e:
                if e.status_code == 529:  # Service overloaded
                    retry_count += 1
                    if retry_count > max_retries:
                        raise PlanGenerationError("Service Claude temporairement indisponible")
                    
                    logger.warning(f"Claude surchargé, retry {retry_count}/{max_retries} dans 30s")
                    asyncio.sleep(30)
                else:
                    logger.error(f"Erreur API Claude {e.status_code}: {e}")
                    raise PlanGenerationError(f"Erreur API Claude: {e}")
                    
            except Exception as e:
                logger.error(f"Erreur inattendue Claude: {e}")
                raise PlanGenerationError(f"Erreur inattendue: {e}")
    
    def _stream_claude_response(
        self,
        prompt: str,
        system_prompt: str,
        on_chunk: Optional[Callable[[str, str], None]] = None
    ) -> str:
        """
        Appelle Claude avec streaming et accumule la réponse.
        """
        try:
            # Créer le stream avec timeout
            with self.client.messages.stream(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                timeout=self.timeout
            ) as stream:
                
                accumulated_text = ""
                input_tokens = 0
                output_tokens = 0
                
                # Traiter le stream
                for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text'):
                            chunk_text = event.delta.text
                            accumulated_text += chunk_text
                            
                            # Callback pour le streaming WebSocket
                            if on_chunk:
                                on_chunk(chunk_text, accumulated_text)
                    
                    elif event.type == "message_start":
                        # Récupérer le comptage des tokens d'input
                        if hasattr(event.message, 'usage'):
                            input_tokens = event.message.usage.input_tokens
                    
                    elif event.type == "message_delta":
                        # Récupérer le comptage final des tokens
                        if hasattr(event.delta, 'usage'):
                            output_tokens = event.delta.usage.output_tokens
                
                # Logger les métriques
                logger.info(
                    f"Claude streaming terminé - "
                    f"Input: {input_tokens} tokens, "
                    f"Output: {output_tokens} tokens, "
                    f"Response length: {len(accumulated_text)}"
                )
                
                return accumulated_text
                
        except anthropic.APITimeoutError:
            raise PlanGenerationError("Timeout lors de l'appel Claude")
    
    def call_claude_sync(self, prompt: str, system_prompt: str) -> str:
        """
        Version synchrone pour les tests et les usages non-streaming.
        Même configuration que call_claude_streaming sans les callbacks.
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                timeout=self.timeout
            )
            
            # Extraire le texte de la réponse
            if message.content and len(message.content) > 0:
                return message.content[0].text
            else:
                raise PlanGenerationError("Réponse Claude vide")
                
        except anthropic.APITimeoutError:
            raise PlanGenerationError("Timeout lors de l'appel Claude")
        except Exception as e:
            logger.error(f"Erreur Claude sync: {e}")
            raise PlanGenerationError(f"Erreur Claude: {e}")
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimation approximative du nombre de tokens.
        Claude utilise un tokenizer différent, mais 4 chars ≈ 1 token est une approximation raisonnable.
        """
        return len(text) // 4
    
    def validate_api_key(self) -> bool:
        """
        Valide que la clé API Claude fonctionne.
        """
        if not settings.ANTHROPIC_API_KEY:
            return False
            
        try:
            # Test simple avec un prompt minimal
            test_response = self.call_claude_sync(
                "Réponds juste 'OK'", 
                "Tu es un assistant de test."
            )
            return "ok" in test_response.lower()
            
        except Exception:
            return False